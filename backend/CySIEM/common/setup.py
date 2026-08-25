"""
Run once after `docker compose up -d` to create all Kafka topics and the
OpenSearch index template. Idempotent - safe to re-run.
"""
import logging
from confluent_kafka.admin import AdminClient, NewTopic
from CySIEM.common.config import settings
from CySIEM.storage.opensearch_client import OpenSearchClient
from CySIEM.storage.object_store_client import ObjectStoreClient

logger = logging.getLogger("kksiem.setup")

TOPICS = [
    settings.topic(settings.topic_raw_windows),
    settings.topic(settings.topic_raw_linux),
    settings.topic(settings.topic_raw_firewall),
    settings.topic(settings.topic_normalized),
    settings.topic(settings.topic_tool_alerts),
    settings.topic(settings.topic_agent1_findings),
    settings.topic(settings.topic_agent2_findings),
    settings.topic(settings.topic_alerts_confirmed),
    settings.topic(settings.topic_human_verdicts),
    settings.topic(settings.topic_dlq),
    settings.topic(settings.topic_quarantine),
]


def run_setup():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    logger.info(f"Connecting to Kafka at {settings.kafka_bootstrap_servers}")
    admin = AdminClient({"bootstrap.servers": settings.kafka_bootstrap_servers})

    existing = admin.list_topics(timeout=10).topics.keys()
    new_topics = [
        NewTopic(t, num_partitions=3, replication_factor=1)
        for t in TOPICS if t not in existing
    ]

    if new_topics:
        futures = admin.create_topics(new_topics)
        for topic, future in futures.items():
            try:
                future.result()
                logger.info(f"Created topic: {topic}")
            except Exception as e:
                logger.warning(f"Could not create topic {topic}: {e}")
    else:
        logger.info("All topics already exist")

    logger.info("Ensuring OpenSearch index template...")
    OpenSearchClient().ensure_index_template()

    logger.info(f"Ensuring object store bucket at {settings.object_store_endpoint_url}...")
    try:
        ObjectStoreClient().ensure_bucket()
    except Exception as e:
        logger.warning(f"Could not ensure object store bucket (MinIO/S3 may not be reachable yet): {e}")

    logger.info("Setup complete. Topics: %s", TOPICS)


if __name__ == "__main__":
    run_setup()
