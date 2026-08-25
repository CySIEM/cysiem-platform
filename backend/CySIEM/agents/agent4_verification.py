"""
Agent 4: Verification.

Called by Agent 3 (not a standalone Kafka consumer loop) with the source_host
that Agent 3 wants to verify. Queries OpenSearch (Layer 0 Evidence Lake) for
that host's historical activity, asks Claude to judge whether the current
finding represents a genuine deviation from baseline or is explainable by
routine activity, and returns a VerificationResult back to Agent 3.

Exposed as `run_verification()` so Agent 3 calls it in-process/synchronously
as part of its escalation flow, matching your described flow: "agent3 will
push alert after agent4 gives output back to agent3".
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from CySIEM.schemas.agent_io import AgentFinding, VerificationResult
from CySIEM.storage.opensearch_client import OpenSearchClient
from CySIEM.intelligence.asset_registry import AssetRegistry
from CySIEM.agents.base import call_claude_structured

logger = logging.getLogger("kksiem.agents.agent4")

SYSTEM_PROMPT = """You are a senior SOC analyst AI performing final
verification before an alert reaches a human. You are given a suspected
malicious finding, the host's historical event baseline (prior 24 hours),
and the host's business context (criticality, asset type). Confirm the
finding if the current activity meaningfully deviates from the host's
normal baseline, OR if the activity is inherently high-risk regardless of
baseline (e.g. successful auth from a known attacker segment, privilege
escalation, known-malicious process names). Weight your decision by asset
criticality: the same ambiguous signal on a 'critical' asset (e.g. a domain
controller) warrants confirmation where it might not on a 'low' criticality
test host - lower your bar for escalation as criticality increases. Dismiss
if the pattern is consistent with routine/expected behavior for this host
AND the asset is not high-value enough to warrant erring cautious. Be
decisive - this is the last check before a human gets paged."""

_opensearch = OpenSearchClient()
_assets = AssetRegistry()

HISTORY_LOOKBACK_HOURS = 24


def run_verification(host: str, f1: AgentFinding | None, f2: AgentFinding | None) -> VerificationResult:
    now = datetime.now(timezone.utc)
    history_start = now - timedelta(hours=HISTORY_LOOKBACK_HOURS)

    history = _opensearch.query_host_history(host, history_start, now, size=200)
    history_summary = "\n".join(
        f"- [{h.get('event_time')}] {h.get('normalized', {}).get('event_category')} "
        f"action={h.get('normalized', {}).get('action')} outcome={h.get('normalized', {}).get('outcome')}"
        for h in history[-50:]   # cap prompt size
    ) or "No prior history found for this host in the lookback window."

    findings_summary = "\n".join(
        f"- {f.agent_name}: verdict={f.verdict} confidence={f.confidence} reasoning={f.reasoning}"
        for f in (f1, f2) if f is not None
    )

    # Layer 2A: asset business context. Falls back to criticality=unknown
    # for unregistered hosts rather than failing - registration lag is
    # expected and shouldn't break verification.
    asset = _assets.get(host)
    asset_summary = (
        f"criticality={asset.criticality.value}, asset_type={asset.asset_type or 'unregistered'}, "
        f"owner={asset.owner or 'unknown'}"
    )

    user_prompt = (
        f"Host: {host}\n"
        f"Asset context: {asset_summary}\n"
        f"Current findings under review:\n{findings_summary}\n\n"
        f"Historical baseline ({HISTORY_LOOKBACK_HOURS}h, {len(history)} events, most recent 50 shown):\n"
        f"{history_summary}\n\n"
        f"Decide: does this confirm genuine malicious/suspicious activity worth alerting a human? "
        f"Set source_host to '{host}' exactly."
    )

    result = call_claude_structured(SYSTEM_PROMPT, user_prompt, VerificationResult)
    result.source_host = host
    if not result.supporting_event_ids and history:
        # fall back to attaching the most recent handful of event_ids as context
        result.supporting_event_ids = [h.get("event_id") for h in history[-10:] if h.get("event_id")]

    logger.info(f"Agent4 verification: host={host} confirmed={result.confirmed}")
    return result
