"""
Agent 3: Consensus (Layer 5 Correlation Fabric entry point).

Consumes BOTH agent1.findings and agent2.findings, joins them on source_host
within a matching time window (this is the practical answer to "how does
Agent 3 know Agent 1 and Agent 2 are talking about the same thing" - they
share the source_host field by construction, enforced in agents/base.py).

Join state lives in Redis (see agents/correlation_store.py), not process
memory - this survives a restart and lets you run multiple Agent 3 replicas
without losing in-flight correlations. This was v1's most significant
loophole: an in-memory dict meant a crash mid-correlation silently dropped
whatever host was pending, with no error and no trace. Externalizing this
state is also the natural shape for v4.1's Layer 5 (Correlation Fabric) as
its own addressable component.

If both agents agree on suspicious/malicious (or one is highly confident),
escalate to Agent 4 for verification. Otherwise, log and drop (still fully
auditable via the *.findings topics themselves).
"""
from __future__ import annotations
import logging
import threading
import time
from CySIEM.common.config import settings
from CySIEM.common.kafka_client import KafkaProducerClient, KafkaConsumerClient
from CySIEM.schemas.agent_io import AgentFinding, ConsensusResult, Verdict, FinalAlert
from CySIEM.agents.agent4_verification import run_verification
from CySIEM.agents.alerting import push_alert
from CySIEM.agents.correlation_store import CorrelationStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kksiem.agents.agent3")

JOIN_WINDOW_SECONDS = settings.correlation_join_window_seconds
HIGH_CONFIDENCE_SOLO_THRESHOLD = 0.9   # allow single-agent escalation if extremely confident


class Agent3Service:
    def __init__(self):
        self.producer = KafkaProducerClient(settings.kafka_bootstrap_servers, client_id="kksiem-agent3")
        # Two separate consumers, one per findings topic, run in threads so
        # either can arrive first without blocking the other.
        self.consumer1 = KafkaConsumerClient(
            settings.kafka_bootstrap_servers, group_id="kksiem-agent3-a1",
            topics=[settings.topic(settings.topic_agent1_findings)],
        )
        self.consumer2 = KafkaConsumerClient(
            settings.kafka_bootstrap_servers, group_id="kksiem-agent3-a2",
            topics=[settings.topic(settings.topic_agent2_findings)],
        )
        self.store = CorrelationStore(ttl_seconds=settings.correlation_ttl_seconds)
        if not self.store.health_check():
            raise RuntimeError(
                "Redis (correlation store) is unreachable at startup. "
                "Agent 3 refuses to start with no durable correlation state - "
                "check REDIS_HOST/REDIS_PORT and that the redis container is up."
            )

    def _record_and_maybe_evaluate(self, finding: AgentFinding, slot: str):
        host = finding.source_host
        try:
            f1, f2, claimed = self.store.record_finding(host, slot, finding)
        except Exception as e:
            # Redis failure mid-correlation: fail loudly, don't silently drop
            # the finding. The Kafka consumer won't commit this offset (see
            # kafka_client.py's on_error handling), so it will be retried.
            logger.error(f"Correlation store write failed for host={host}: {e}")
            raise

        solo_high_conf = not claimed and finding.confidence >= HIGH_CONFIDENCE_SOLO_THRESHOLD \
            and finding.verdict != Verdict.BENIGN

        if claimed:
            self._evaluate(host, f1, f2)
        elif solo_high_conf:
            # extremely confident single-agent signal - don't wait for the
            # partner finding, but leave the stored entry alone (partner may
            # still arrive later and that's fine, sweep will just find it empty)
            self._evaluate(host, finding if slot == "agent1" else None,
                            finding if slot == "agent2" else None)

    def _evaluate(self, host: str, f1: AgentFinding | None, f2: AgentFinding | None):
        non_benign = [f for f in (f1, f2) if f and f.verdict != Verdict.BENIGN]
        agreement = f1 is not None and f2 is not None and \
            f1.verdict != Verdict.BENIGN and f2.verdict != Verdict.BENIGN

        if not non_benign:
            logger.info(f"Consensus: host={host} both benign, no escalation")
            return

        combined_confidence = sum(f.confidence for f in non_benign) / len(non_benign)
        escalate = agreement or combined_confidence >= HIGH_CONFIDENCE_SOLO_THRESHOLD

        segment = (f1 or f2).source_segment

        result = ConsensusResult(
            source_host=host,
            source_segment=segment,
            agent1_finding=f1,
            agent2_finding=f2,
            agreement=agreement,
            combined_confidence=round(combined_confidence, 2),
            escalate_to_verification=escalate,
            rationale=(
                f"Agent1={f1.verdict if f1 else 'n/a'} Agent2={f2.verdict if f2 else 'n/a'}; "
                f"{'agreement' if agreement else 'single high-confidence signal'}"
            ),
        )

        logger.info(
            f"Consensus: host={host} escalate={escalate} confidence={result.combined_confidence}"
        )

        if not escalate:
            return

        # Agent 4: verify against Evidence Lake before alerting
        try:
            verification = run_verification(host, f1, f2)
        except Exception as e:
            logger.error(f"Agent4 verification failed for host={host}: {e}")
            return

        if verification.confirmed:
            evidence_ids = list(set(
                (f1.evidence_event_ids if f1 else []) +
                (f2.evidence_event_ids if f2 else []) +
                verification.supporting_event_ids
            ))
            mitre = list(set((f1.mitre_techniques if f1 else []) + (f2.mitre_techniques if f2 else [])))

            alert = FinalAlert(
                source_host=host,
                source_segment=segment,
                severity="high" if combined_confidence >= 0.85 else "medium",
                title=f"Confirmed suspicious activity on {host}",
                summary=verification.reasoning,
                agent1_summary=f1.reasoning if f1 else "N/A - no tool alert corroboration",
                agent2_summary=f2.reasoning if f2 else "N/A - no direct log finding",
                verification_summary=verification.reasoning,
                mitre_techniques=mitre,
                evidence_event_ids=evidence_ids,
            )
            push_alert(alert)
            self.producer.send(settings.topic(settings.topic_alerts_confirmed), value=alert, key=host)
            logger.warning(f"ALERT PUSHED: host={host} severity={alert.severity}")
        else:
            logger.info(f"Agent4 dismissed escalation for host={host}: {verification.reasoning}")

    def _sweep_expired(self):
        """Findings that waited past JOIN_WINDOW_SECONDS without a partner
        get evaluated solo rather than silently discarded. Runs against
        Redis, so this works correctly even with multiple Agent 3 replicas -
        each sweep tick claims entries atomically via GETDEL, so two
        replicas can't both evaluate the same stale host."""
        while True:
            time.sleep(15)
            try:
                expired = self.store.sweep_expired(min_age_seconds=JOIN_WINDOW_SECONDS)
            except Exception as e:
                logger.error(f"Correlation sweep failed: {e}")
                continue
            for host, f1, f2 in expired:
                self._evaluate(host, f1, f2)

    def run(self):
        logger.info("Agent3 (consensus) starting...")
        threading.Thread(target=self._sweep_expired, daemon=True).start()
        threading.Thread(
            target=self.consumer1.poll_loop,
            args=(lambda parsed, key: self._record_and_maybe_evaluate(AgentFinding(**parsed), "agent1"),),
            daemon=True,
        ).start()
        # main thread runs consumer2 (blocking)
        self.consumer2.poll_loop(
            lambda parsed, key: self._record_and_maybe_evaluate(AgentFinding(**parsed), "agent2")
        )


if __name__ == "__main__":
    Agent3Service().run()
