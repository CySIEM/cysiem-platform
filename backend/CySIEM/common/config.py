"""
Centralized configuration for KKSIEM.
All services (normalizer, detection consumers, agents, API) import from here.
Values are read from environment variables / .env file so the same codebase
runs unmodified in dev, docker-compose, or on the OPT4 KKSIEM host.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- Tenancy ----
    # Every install runs as exactly one tenant today (single-install
    # deployment model). This is deliberately a real, required value - not
    # a feature flag - so a future multi-tenant SaaS path (many installs ->
    # one cluster, many tenant_ids) is a deployment change, not a rewrite.
    # Collectors stamp this into every RawMessage; the normalizer never
    # invents or defaults it.
    tenant_id: str = "default"

    # ---- Kafka ----
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group_normalizer: str = "kksiem-normalizer"
    kafka_consumer_group_agent1: str = "kksiem-agent1"
    kafka_consumer_group_agent2: str = "kksiem-agent2"

    # Raw topic BASE names (one per source type, written to by collectors).
    # Actual topic names are tenant-namespaced via topic() below, e.g.
    # "default.raw.windows" - a consumer subscribed to one tenant's topics
    # physically cannot receive another tenant's messages.
    topic_raw_windows: str = "raw.windows"
    topic_raw_linux: str = "raw.linux"
    topic_raw_firewall: str = "raw.firewall"

    # Canonical topic (written to by the normalizer, read by everyone downstream)
    topic_normalized: str = "normalized.events"

    # Detection tool alerts topic (Path A)
    topic_tool_alerts: str = "tool.alerts"

    # Agent finding topics
    topic_agent1_findings: str = "agent1.findings"
    topic_agent2_findings: str = "agent2.findings"
    topic_alerts_confirmed: str = "alerts.confirmed"

    # Human review verdicts (v4.1 Layer 9 -> Layer 11 bridge). Captured now,
    # even though nothing consumes it yet, so the day Layer 11 (Learning
    # Fabric) is built there is already a historical dataset of analyst
    # true-positive/false-positive verdicts to train against - not starting
    # from zero.
    topic_human_verdicts: str = "human.verdicts"

    # Dead letter queue: messages that FAILED TO PARSE (malformed JSON,
    # missing required field) - never became a valid RawMessage at all.
    topic_dlq: str = "dlq.normalizer"

    # Quarantine queue: messages that parsed fine and became a valid
    # CanonicalEvent, but routing.py's data-quality/timestamp checks
    # flagged something suspect. Distinct from DLQ - this is a "review me"
    # signal on usable data, not a parse failure.
    topic_quarantine: str = "quarantine.normalizer"

    def topic(self, base: str, tenant_id: str | None = None) -> str:
        """Tenant-namespace a base topic name: topic('raw.windows') ->
        'default.raw.windows'. Use this everywhere a topic name is needed
        instead of the bare topic_* string, so every call site is
        tenant-correct by construction."""
        return f"{tenant_id or self.tenant_id}.{base}"

    # ---- OpenSearch ----
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_use_ssl: bool = False
    opensearch_index_prefix: str = "kksiem-events"
    # Separate index prefix for quarantined events, so a query against the
    # normal event indices never silently includes flagged/suspect data
    # unless explicitly asked for.
    opensearch_quarantine_index_prefix: str = "kksiem-quarantine"

    # ---- Object Storage (Layer 0 cold tier) ----
    # LOCAL (default): points at MinIO running in docker-compose.
    # CLOUD LATER: change object_store_endpoint_url to your S3/R2/B2/Wasabi
    # endpoint (or omit it entirely for real AWS S3, which needs no custom
    # endpoint) and swap credentials - no code changes required anywhere,
    # since object_store_client.py is written against the S3 API via boto3.
    object_store_endpoint_url: str = "http://localhost:9000"   # MinIO default; set to "" for real AWS S3
    object_store_access_key: str = "kksiem-admin"
    object_store_secret_key: str = "kksiem-secret-change-me"
    object_store_bucket: str = "kksiem-evidence-lake"
    object_store_region: str = "us-east-1"   # required by boto3 even for MinIO; harmless locally

    # ---- Redis (Agent 3 correlation state, Asset Registry, Dedup store) ----
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    correlation_ttl_seconds: int = 300
    correlation_join_window_seconds: int = 120

    # ---- Deduplication (Layer 1) ----
    # How long a content-hash fingerprint is remembered in Redis before it
    # expires and an identical-looking event is allowed through again as
    # new. Set above the longest realistic collector retry/restart window,
    # but short enough that a legitimately recurring identical log line
    # (e.g. a daily cron's fixed output) isn't permanently suppressed.
    dedup_window_seconds: int = 3600


    # ---- Batch JSON Export (Layer 2) ----
    # Independent, toggleable side-channel: buffers normalized events and
    # periodically writes them to local .json files, IN ADDITION to the
    # real-time Kafka/OpenSearch path. Disabling this has zero effect on
    # ingestion/detection - it's purely an export/archive convenience.
    # See kksiem/normalizer/batch_export.py for window/restart behavior.
    batch_export_enabled: bool = True
    batch_export_output_dir: str = "/home/light/code/logs"
    batch_export_window_seconds: int = 1800  # 30 minutes

    # ---- Anthropic ----
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # ---- Alerting ----
    slack_webhook_url: str = ""

    # ---- Known hosts (segment mapping fallback if collector didn't tag it) ----
    # host_ip -> (segment, host_type) resolved at normalize time if missing
    known_segments: dict = {
        "192.168.10": "LAN",
        "192.168.20": "OPT1",
        "192.168.30": "OPT2",
        "192.168.40": "OPT3",
        "192.168.50": "OPT4",
    }


settings = Settings()






















































# """
# Centralized configuration for KKSIEM.
# All services (normalizer, detection consumers, agents, API) import from here.
# Values are read from environment variables / .env file so the same codebase
# runs unmodified in dev, docker-compose, or on the OPT4 KKSIEM host.
# """
# from pydantic_settings import BaseSettings, SettingsConfigDict
# from typing import List


# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    

#     # ---- Kafka ----
#     kafka_bootstrap_servers: str = "localhost:9092"
#     kafka_consumer_group_normalizer: str = "kksiem-normalizer"
#     kafka_consumer_group_agent1: str = "kksiem-agent1"
#     kafka_consumer_group_agent2: str = "kksiem-agent2"

#     # Raw topics (one per source type, written to by collectors)
#     topic_raw_windows: str = "raw.windows"
#     topic_raw_linux: str = "raw.linux"
#     topic_raw_firewall: str = "raw.firewall"

#     # Canonical topic (written to by the normalizer, read by everyone downstream)
#     topic_normalized: str = "normalized.events"

#     # Detection tool alerts topic (Path A)
#     topic_tool_alerts: str = "tool.alerts"

#     # Agent finding topics
#     topic_agent1_findings: str = "agent1.findings"
#     topic_agent2_findings: str = "agent2.findings"
#     topic_alerts_confirmed: str = "alerts.confirmed"

#     # Human review verdicts (v4.1 Layer 9 -> Layer 11 bridge). Captured now,
#     # even though nothing consumes it yet, so the day Layer 11 (Learning
#     # Fabric) is built there is already a historical dataset of analyst
#     # true-positive/false-positive verdicts to train against - not starting
#     # from zero.
#     topic_human_verdicts: str = "human.verdicts"

#     # Dead letter queue for anything that fails to parse/normalize
#     topic_dlq: str = "dlq.normalizer"

#     # ---- OpenSearch ----
#     opensearch_host: str = "localhost"
#     opensearch_port: int = 9200
#     opensearch_use_ssl: bool = False
#     opensearch_index_prefix: str = "kksiem-events"

#     # ---- Object Storage (Layer 0 cold tier) ----
#     # LOCAL (default): points at MinIO running in docker-compose.
#     # CLOUD LATER: change object_store_endpoint_url to your S3/R2/B2/Wasabi
#     # endpoint (or omit it entirely for real AWS S3, which needs no custom
#     # endpoint) and swap credentials - no code changes required anywhere,
#     # since object_store_client.py is written against the S3 API via boto3.
#     object_store_endpoint_url: str = "http://localhost:9000"   # MinIO default; set to "" for real AWS S3
#     object_store_access_key: str = "kksiem-admin"
#     object_store_secret_key: str = "kksiem-secret-change-me"
#     object_store_bucket: str = "kksiem-evidence-lake"
#     object_store_region: str = "us-east-1"   # required by boto3 even for MinIO; harmless locally

#     # ---- Redis (Agent 3 correlation state - Layer 5 concern) ----
#     redis_host: str = "localhost"
#     redis_port: int = 6379
#     redis_db: int = 0
#     correlation_ttl_seconds: int = 300
#     correlation_join_window_seconds: int = 120
    

#     # ---- Anthropic ----
#     anthropic_api_key: str = ""
#     anthropic_model: str = "claude-sonnet-4-6"

#     # ---- Alerting ----
#     slack_webhook_url: str = ""

#     # ---- Known hosts (segment mapping fallback if collector didn't tag it) ----
#     # host_ip -> (segment, host_type) resolved at normalize time if missing
#     known_segments: dict = {
#         "192.168.10": "LAN",
#         "192.168.20": "OPT1",
#         "192.168.30": "OPT2",
#         "192.168.40": "OPT3",
#         "192.168.50": "OPT4",
#     }


# settings = Settings()
