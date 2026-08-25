"""
Bridges Suricata's eve.json alert log into the tool.alerts Kafka topic that
Agent 1 consumes. This is Path A's entry point: Suricata does the actual
detection (signature match), this script's only job is to tail the file,
extract host identity + alert details, and publish in the shape Agent 1
expects (source_host, source_segment, tool, signature, severity, details).

Run with: python -m kksiem.detection.suricata_bridge
Requires HOST_NAME / HOST_SEGMENT env vars set for the machine Suricata is
running on (same pattern as the Fluent Bit linux config).
"""
from __future__ import annotations
import json
import logging
import os
import time
from CySIEM.common.config import settings
from CySIEM.common.kafka_client import KafkaProducerClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kksiem.detection.suricata_bridge")

EVE_JSON_PATH = os.environ.get("SURICATA_EVE_PATH", "/var/log/suricata/eve.json")
HOST_NAME = os.environ.get("HOST_NAME", "unknown-host")
HOST_SEGMENT = os.environ.get("HOST_SEGMENT", "UNKNOWN")


def tail_f(path: str):
    with open(path, "r") as f:
        f.seek(0, 2)  # seek to end, only new lines
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            yield line


def main():
    producer = KafkaProducerClient(settings.kafka_bootstrap_servers, client_id="suricata-bridge")
    logger.info(f"Tailing {EVE_JSON_PATH} for host={HOST_NAME} segment={HOST_SEGMENT}")

    for line in tail_f(EVE_JSON_PATH):
        try:
            event = json.loads(line)
            if event.get("event_type") != "alert":
                continue

            alert = event.get("alert", {})
            payload = {
                "source_host": HOST_NAME,
                "source_segment": HOST_SEGMENT,
                "tool": "suricata",
                "signature": alert.get("signature"),
                "severity": alert.get("severity"),
                "rule_name": alert.get("signature_id"),
                "timestamp": event.get("timestamp"),
                "details": {
                    "src_ip": event.get("src_ip"),
                    "dest_ip": event.get("dest_ip"),
                    "proto": event.get("proto"),
                    "category": alert.get("category"),
                },
            }
            producer.send(settings.topic(settings.topic_tool_alerts), value=payload, key=HOST_NAME)
            logger.info(f"Forwarded Suricata alert: {alert.get('signature')}")
        except json.JSONDecodeError:
            continue
        except Exception as e:
            logger.error(f"Failed to process eve.json line: {e}")


if __name__ == "__main__":
    main()
