"""
Agent 2: AI-native log analyzer (Path B).
Consumes `normalized.events` directly (no detection tool involved), buffers
events per-host into small time windows, and asks Claude to assess whether
the pattern within that window looks suspicious. Emits AgentFinding, keyed
on source_host - the join key Agent 3 needs.
"""
from __future__ import annotations
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from CySIEM.common.config import settings
from CySIEM.common.kafka_client import KafkaProducerClient, KafkaConsumerClient
from CySIEM.schemas.agent_io import AgentFinding, Verdict
from CySIEM.schemas.canonical import assert_supported_version, SchemaVersionError
from CySIEM.agents.base import call_claude_structured

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kksiem.agents.agent2")

WINDOW_SECONDS = 60           # how much time we buffer per host before asking Claude
MIN_EVENTS_TO_ANALYZE = 3     # don't bother calling the model for 1-2 mundane events

SYSTEM_PROMPT = """You are a SOC analyst AI reviewing a short window of raw,
normalized security events for a single host. Determine if this activity
looks benign, suspicious, or malicious. Consider authentication failures,
unusual process chains, unexpected network connections, and privilege
changes. Be conservative: only flag 'malicious' with strong evidence, use
'suspicious' for patterns worth a human look, and 'benign' otherwise."""


class Agent2Service:
    def __init__(self):
        self.producer = KafkaProducerClient(settings.kafka_bootstrap_servers, client_id="kksiem-agent2")
        self.consumer = KafkaConsumerClient(
            settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group_agent2,
            topics=[settings.topic(settings.topic_normalized)],
        )
        # host -> list of event dicts buffered for the current window
        self.buffers: dict[str, list[dict]] = defaultdict(list)
        self.window_start: dict[str, datetime] = {}

    def handle_message(self, parsed: dict, key: str | None):
        # Enforce schema version BEFORE trusting the shape of `parsed`. If
        # v4.1 (or any future change) bumps CURRENT_SCHEMA_VERSION and this
        # consumer hasn't been updated to understand it, we route to DLQ
        # instead of crashing on a missing/renamed field or - worse -
        # silently misreading a field that changed meaning.
        try:
            assert_supported_version(parsed.get("schema_version", "unknown"))
        except SchemaVersionError as e:
            logger.warning(f"Dropping unsupported schema version event: {e}")
            self.producer.send(settings.topic(settings.topic_dlq), value={"error": str(e), "event": parsed})
            return

        host = parsed["source"]["host"]
        now = datetime.now(timezone.utc)

        if host not in self.window_start:
            self.window_start[host] = now

        self.buffers[host].append(parsed)

        elapsed = (now - self.window_start[host]).total_seconds()
        if elapsed >= WINDOW_SECONDS and len(self.buffers[host]) >= MIN_EVENTS_TO_ANALYZE:
            self._analyze_window(host)

    def _analyze_window(self, host: str):
        events = self.buffers.pop(host)
        window_start = self.window_start.pop(host)
        window_end = datetime.now(timezone.utc)

        segment = events[0]["source"].get("segment", "UNKNOWN")
        event_summaries = "\n".join(
            f"- [{e['event_time']}] category={e['normalized']['event_category']} "
            f"action={e['normalized'].get('action')} user={e['normalized'].get('user')} "
            f"src_ip={e['normalized'].get('src_ip')} outcome={e['normalized'].get('outcome')} "
            f"event_id={e['event_id']}"
            for e in events
        )
        user_prompt = (
            f"Host: {host} (segment: {segment})\n"
            f"Window: {window_start.isoformat()} to {window_end.isoformat()}\n"
            f"Events ({len(events)}):\n{event_summaries}\n\n"
            f"Assess this activity. Include the event_id values that support your reasoning "
            f"in evidence_event_ids. Set source_host to '{host}' and source_segment to '{segment}' exactly."
        )

        try:
            finding = call_claude_structured(SYSTEM_PROMPT, user_prompt, AgentFinding)
            finding.agent_name = "agent2_log_analyzer"
            finding.source_host = host  # enforce, don't trust the model blindly
            finding.window_start = window_start
            finding.window_end = window_end

            self.producer.send(settings.topic(settings.topic_agent2_findings), value=finding, key=host)
            logger.info(f"Agent2 finding: host={host} verdict={finding.verdict} conf={finding.confidence}")

            if finding.verdict in (Verdict.SUSPICIOUS, Verdict.MALICIOUS):
                # Agent 3 only needs to react to non-benign findings; still
                # publishing all findings above keeps a full audit trail.
                pass
        except Exception as e:
            logger.error(f"Agent2 analysis failed for host={host}: {e}")

    def flush_stale_windows(self):
        """Catch hosts that never hit MIN_EVENTS_TO_ANALYZE but have an
        old window open - analyze whatever's there so nothing sits forever."""
        now = datetime.now(timezone.utc)
        stale = [h for h, ws in self.window_start.items() if (now - ws).total_seconds() >= WINDOW_SECONDS * 3]
        for host in stale:
            if self.buffers[host]:
                self._analyze_window(host)
            else:
                self.window_start.pop(host, None)

    def run(self):
        logger.info("Agent2 (log analyzer) starting...")
        last_flush_check = time.time()

        def handler_with_flush(parsed, key):
            self.handle_message(parsed, key)
            nonlocal last_flush_check
            if time.time() - last_flush_check > 30:
                self.flush_stale_windows()
                last_flush_check = time.time()

        self.consumer.poll_loop(handler_with_flush)


if __name__ == "__main__":
    Agent2Service().run()
