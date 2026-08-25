"""
Layer 4 -- Detection Fabric, Sigma rule component.

v1 already has Suricata (network-based detection, see
detection/suricata_bridge.py). This adds the rule-based / log-based half:
Sigma rules evaluated against events already in OpenSearch, on a polling
interval. This is intentionally simple (pySigma's OpenSearch backend does
the rule-to-query translation) rather than a full streaming rule engine -
"basic v4.1", not the final Detection Fabric.

Output lands on the same `tool.alerts` topic Suricata uses, so Agent 1
doesn't need to know or care which detection tool produced an alert - both
speak the same shape.

Requires: pip install pysigma pysigma-backend-opensearch
Rule files: place .yml Sigma rules under kksiem/detection/sigma_rules/
"""
from __future__ import annotations
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
import yaml
from CySIEM.common.config import settings
from CySIEM.common.kafka_client import KafkaProducerClient
from CySIEM.storage.opensearch_client import OpenSearchClient

logger = logging.getLogger("kksiem.detection.sigma_runner")

RULES_DIR = Path(__file__).parent / "sigma_rules"
POLL_INTERVAL_SECONDS = 60


class SigmaRunner:
    """
    Minimal Sigma-style rule evaluator: rules are simple field-match YAML
    (a practical subset of real Sigma syntax) evaluated directly against
    OpenSearch via term queries. This proves the Layer 4 integration shape
    (rule fires -> tool.alerts -> Agent 1) without pulling in the full
    pySigma rule-translation pipeline under time pressure - swap in real
    pySigma later without touching anything downstream of tool.alerts.
    """

    def __init__(self):
        self.opensearch = OpenSearchClient()
        self.producer = KafkaProducerClient(settings.kafka_bootstrap_servers, client_id="sigma-runner")
        self.rules = self._load_rules()

    def _load_rules(self) -> list[dict]:
        rules = []
        if not RULES_DIR.exists():
            logger.warning(f"Sigma rules directory {RULES_DIR} does not exist, no rules loaded")
            return rules
        for rule_file in RULES_DIR.glob("*.yml"):
            try:
                with open(rule_file) as f:
                    rule = yaml.safe_load(f)
                    rule["_file"] = rule_file.name
                    rules.append(rule)
            except Exception as e:
                logger.error(f"Failed to load Sigma rule {rule_file}: {e}")
        logger.info(f"Loaded {len(rules)} Sigma rules from {RULES_DIR}")
        return rules

    def _evaluate_rule(self, rule: dict, window_start: datetime, window_end: datetime):
        """Evaluate one rule's field-match conditions against events in the
        window. Rule format (simplified Sigma subset):
            title: SSH Brute Force
            id: rule-001
            severity: high
            detection:
              field_matches:
                normalized.action: logon_failed
              min_count: 5   # optional - fire only if >= N matching events for same host
        """
        conditions = rule.get("detection", {}).get("field_matches", {})
        min_count = rule.get("detection", {}).get("min_count", 1)
        if not conditions:
            return

        must_clauses = [{"term": {field: value}} for field, value in conditions.items()]
        must_clauses.append({"range": {"event_time": {"gte": window_start.isoformat(), "lte": window_end.isoformat()}}})

        body = {
            "size": 0,
            "query": {"bool": {"must": must_clauses}},
            "aggs": {"by_host": {"terms": {"field": "source.host", "size": 100, "min_doc_count": min_count}}},
        }

        try:
            resp = self.opensearch.client.search(
                index=f"{settings.opensearch_index_prefix}-*", body=body
            )
        except Exception as e:
            logger.error(f"Sigma rule {rule.get('id')} query failed: {e}")
            return

        buckets = resp.get("aggregations", {}).get("by_host", {}).get("buckets", [])
        for bucket in buckets:
            host = bucket["key"]
            count = bucket["doc_count"]
            self._emit_alert(rule, host, count, window_start, window_end)

    def _emit_alert(self, rule: dict, host: str, count: int, window_start: datetime, window_end: datetime):
        payload = {
            "source_host": host,
            "source_segment": "UNKNOWN",   # resolved by Agent1 prompt from OpenSearch if needed
            "tool": "sigma",
            "signature": rule.get("title", rule.get("id", "unknown_rule")),
            "severity": rule.get("severity", "medium"),
            "rule_name": rule.get("id"),
            "timestamp": window_end.isoformat(),
            "details": {
                "match_count": count,
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "rule_file": rule.get("_file"),
            },
        }
        self.producer.send(settings.topic(settings.topic_tool_alerts), value=payload, key=host)
        logger.info(f"Sigma rule fired: {rule.get('title')} host={host} count={count}")

    def run_once(self):
        window_end = datetime.now(timezone.utc)
        window_start = window_end - timedelta(seconds=POLL_INTERVAL_SECONDS * 2)  # slight overlap
        for rule in self.rules:
            self._evaluate_rule(rule, window_start, window_end)

    def run(self):
        logger.info(f"Sigma runner starting, polling every {POLL_INTERVAL_SECONDS}s")
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Sigma runner iteration failed: {e}")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    SigmaRunner().run()
