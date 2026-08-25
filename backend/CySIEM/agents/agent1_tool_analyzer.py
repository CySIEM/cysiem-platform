"""
Agent 1: Tool-based detection analyzer (Path A).
Consumes `tool.alerts` - alerts already produced by Suricata/Wazuh/Sigma
(see detection/tool_alert_schema.py for the expected shape those tools'
outputs get normalized into before landing on this topic). Asks Claude to
assess severity/context across alerts for the same host, emits AgentFinding
using the same schema as Agent 2 so Agent 3 can join them directly.
"""
from __future__ import annotations
import logging
from collections import defaultdict
from datetime import datetime, timezone
from CySIEM.common.config import settings
from CySIEM.common.kafka_client import KafkaProducerClient, KafkaConsumerClient
from CySIEM.schemas.agent_io import AgentFinding
from CySIEM.agents.base import call_claude_structured

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kksiem.agents.agent1")

SYSTEM_PROMPT = """You are a SOC analyst AI reviewing alerts already flagged
by detection tools (Suricata, Wazuh, Sigma rules) for a single host. Your
job is to reduce false positives: tool alerts fire on known patterns but
often lack context. Corroborate whether these alerts, taken together,
represent real malicious activity, or are likely noise (e.g. a single
Suricata signature hit with no follow-through). Be conservative."""


class Agent1Service:
    def __init__(self):
        self.producer = KafkaProducerClient(settings.kafka_bootstrap_servers, client_id="kksiem-agent1")
        self.consumer = KafkaConsumerClient(
            settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group_agent1,
            topics=[settings.topic(settings.topic_tool_alerts)],
        )

    def handle_message(self, parsed: dict, key: str | None):
        host = parsed.get("source_host") or parsed.get("host")
        segment = parsed.get("source_segment", "UNKNOWN")
        tool_name = parsed.get("tool", "unknown_tool")

        user_prompt = (
            f"Host: {host} (segment: {segment})\n"
            f"Detection tool: {tool_name}\n"
            f"Alert: {parsed.get('signature', parsed.get('rule_name', 'unknown'))}\n"
            f"Severity (tool-reported): {parsed.get('severity', 'unknown')}\n"
            f"Details: {parsed.get('details', parsed)}\n"
            f"Timestamp: {parsed.get('timestamp', datetime.now(timezone.utc).isoformat())}\n\n"
            f"Assess whether this represents genuine malicious activity. "
            f"Set source_host to '{host}' and source_segment to '{segment}' exactly."
        )

        try:
            now = datetime.now(timezone.utc)
            finding = call_claude_structured(SYSTEM_PROMPT, user_prompt, AgentFinding)
            finding.agent_name = "agent1_tool_analyzer"
            finding.source_host = host
            finding.window_start = now
            finding.window_end = now

            self.producer.send(settings.topic(settings.topic_agent1_findings), value=finding, key=host)
            logger.info(f"Agent1 finding: host={host} verdict={finding.verdict} conf={finding.confidence}")
        except Exception as e:
            logger.error(f"Agent1 analysis failed for host={host}: {e}")

    def run(self):
        logger.info("Agent1 (tool-output analyzer) starting...")
        self.consumer.poll_loop(self.handle_message)


if __name__ == "__main__":
    Agent1Service().run()
