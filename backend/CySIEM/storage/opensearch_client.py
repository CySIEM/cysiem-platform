"""
OpenSearch client wrapper for Layer 0 (Evidence Lake).
Used by: the normalizer (to index canonical events) and Agent 4 (to query
historical context for a given host during verification).

BUGFIX (this revision): index_event() previously took only (self, event)
with no way to target a different index prefix, but the normalizer's
quarantine write path needs to send flagged events to a SEPARATE index
(settings.opensearch_quarantine_index_prefix) than clean events. Calling
index_event(event, index_prefix=...) against the old signature was a
guaranteed TypeError on every quarantine write. index_event now accepts an
optional index_prefix, defaulting to the normal event index, so existing
"clean path" call sites are unaffected.

MULTI-TENANCY (this revision): query methods now scope to ONE tenant's
index pattern (kksiem-events-{tenant}-*) instead of the bare
kksiem-events-* pattern spanning every tenant, matching
CanonicalEvent.index_name()'s tenant-namespaced naming. A caller cannot
accidentally search across tenants just by forgetting a filter.
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
from CySIEM.common.config import settings
from CySIEM.schemas.canonical import CanonicalEvent

logger = logging.getLogger("kksiem.storage.opensearch")

INDEX_TEMPLATE_NAME = "kksiem-events-template"
QUARANTINE_INDEX_TEMPLATE_NAME = "kksiem-quarantine-template"


class OpenSearchClient:
    def __init__(self):
        self.client = OpenSearch(
            hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}],
            http_compress=True,
            use_ssl=settings.opensearch_use_ssl,
            verify_certs=False,
            connection_class=RequestsHttpConnection,
        )

    def _event_mapping(self) -> dict:
        return {
            "properties": {
                "event_id": {"type": "keyword"},
                "event_time": {"type": "date"},
                "ingested_at": {"type": "date"},
                "source": {
                    "properties": {
                        "tenant_id": {"type": "keyword"},
                        "host": {"type": "keyword"},
                        "ip": {"type": "ip", "ignore_malformed": True},
                        "segment": {"type": "keyword"},
                        "source_type": {"type": "keyword"},
                        "log_type": {"type": "keyword"},
                        "collector": {"type": "keyword"},
                    }
                },
                "normalized": {
                    "properties": {
                        "event_category": {"type": "keyword"},
                        "action": {"type": "keyword"},
                        "user": {"type": "keyword"},
                        "process_name": {"type": "keyword"},
                        "src_ip": {"type": "ip", "ignore_malformed": True},
                        "dest_ip": {"type": "ip", "ignore_malformed": True},
                        "outcome": {"type": "keyword"},
                        "message": {"type": "text"},
                    }
                },
                "raw": {"type": "text"},
            }
        }

    def ensure_index_template(self):
        """Create index templates once so every daily index
        (kksiem-events-{tenant}-2026.07.14, etc) gets consistent mappings.
        Pattern is kksiem-events-* / kksiem-quarantine-* (all tenants) so
        ONE template each covers every tenant's indices - mappings are
        shared, but the underlying indices stay physically separate per
        tenant (see CanonicalEvent.index_name)."""
        body = {
            "index_patterns": [f"{settings.opensearch_index_prefix}-*"],
            "template": {
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": self._event_mapping(),
            },
        }
        quarantine_body = {
            "index_patterns": [f"{settings.opensearch_quarantine_index_prefix}-*"],
            "template": {
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": self._event_mapping(),
            },
        }
        try:
            self.client.indices.put_index_template(name=INDEX_TEMPLATE_NAME, body=body)
            self.client.indices.put_index_template(name=QUARANTINE_INDEX_TEMPLATE_NAME, body=quarantine_body)
            logger.info("OpenSearch index templates ensured (events + quarantine)")
        except Exception as e:
            logger.error(f"Failed to create index template: {e}")

    def index_event(self, event: CanonicalEvent, index_prefix: Optional[str] = None):
        """index_prefix defaults to the normal clean-event prefix; pass
        settings.opensearch_quarantine_index_prefix to write a quarantined
        event into its own separate index instead."""
        prefix = index_prefix or settings.opensearch_index_prefix
        index = event.index_name(prefix)
        try:
            self.client.index(index=index, id=event.event_id, body=event.to_opensearch_doc())
        except Exception as e:
            logger.error(f"Failed to index event {event.event_id} into {index}: {e}")
            raise

    def bulk_index(self, events: list[CanonicalEvent], index_prefix: Optional[str] = None):
        prefix = index_prefix or settings.opensearch_index_prefix
        actions = [
            {
                "_index": e.index_name(prefix),
                "_id": e.event_id,
                "_source": e.to_opensearch_doc(),
            }
            for e in events
        ]
        helpers.bulk(self.client, actions)

    def _tenant_index_pattern(self, tenant_id: str | None = None) -> str:
        return f"{settings.opensearch_index_prefix}-{tenant_id or settings.tenant_id}-*"

    def query_host_history(self, host: str, start: datetime, end: datetime, size: int = 200,
                            tenant_id: str | None = None) -> list[dict]:
        """Used by Agent 4 to pull historical events for a host within a
        time window - the core 'verify against Evidence Lake' operation."""
        body = {
            "size": size,
            "sort": [{"event_time": "asc"}],
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"source.host": host}},
                        {"range": {"event_time": {"gte": start.isoformat(), "lte": end.isoformat()}}},
                    ]
                }
            },
        }
        resp = self.client.search(index=self._tenant_index_pattern(tenant_id), body=body)
        return [hit["_source"] for hit in resp["hits"]["hits"]]

    def get_events_by_ids(self, event_ids: list[str], tenant_id: str | None = None) -> list[dict]:
        if not event_ids:
            return []
        body = {"query": {"terms": {"event_id": event_ids}}, "size": len(event_ids)}
        resp = self.client.search(index=self._tenant_index_pattern(tenant_id), body=body)
        return [hit["_source"] for hit in resp["hits"]["hits"]]
