"""
Layer 2A -- Asset Intelligence.

A minimal but real asset registry: maps hostnames to business context
(criticality, owner, asset type) that pure log data can never contain on
its own. This context matters a lot for triage - a failed login on a
domain controller and the same failed login on a test VM are not the same
severity, and nothing in the raw log tells you that.

Storage: Redis hash, reusing the Redis instance already required for
Agent 3's correlation store, so no new infrastructure for this basic
version. If this grows into a full CMDB integration later, swap the
backend without touching the interface below.

Integration point: normalizer/service.py calls enrich() after building the
CanonicalEvent and before writing it, populating event.extensions["asset"].
This is exactly the forward-compatible seam `extensions` was built for -
v1 consumers that don't check extensions.asset keep working unmodified;
Agent 2/Agent 4 prompts can start using it once it's populated.

MULTI-TENANCY (this revision): every key is now tenant-scoped
(kksiem:assets:{tenant_id}:{host} instead of kksiem:assets:{host}).
Previously two tenants with a host literally named the same thing (e.g.
both naming a box "WIN-SRV01") would silently share and overwrite one
asset record - tenant A's criticality/owner data could be clobbered by
tenant B upserting their own "WIN-SRV01". tenant_id defaults to
settings.tenant_id when omitted, matching the single-install deployment
model where every call site implicitly means "this install's tenant".
"""
from __future__ import annotations
import json
import logging
from enum import Enum
from typing import Optional, List
import redis
from pydantic import BaseModel, Field
from CySIEM.common.config import settings

logger = logging.getLogger("kksiem.intelligence.asset_registry")

ASSET_KEY_PREFIX = "kksiem:assets:"


class Criticality(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class AssetRecord(BaseModel):
    host: str
    criticality: Criticality = Criticality.UNKNOWN
    owner: Optional[str] = None
    asset_type: Optional[str] = None
    segment: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class AssetRegistry:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.redis_host, port=settings.redis_port, db=settings.redis_db,
            decode_responses=True,
        )

    def _key(self, tenant_id: str, host: str) -> str:
        return f"{ASSET_KEY_PREFIX}{tenant_id}:{host}"

    def upsert(self, record: AssetRecord, tenant_id: str = None):
        tenant_id = tenant_id or settings.tenant_id
        self.redis.set(self._key(tenant_id, record.host), record.model_dump_json())
        logger.info(f"Asset registered: tenant={tenant_id} host={record.host} criticality={record.criticality}")

    def get(self, host: str, tenant_id: str = None) -> AssetRecord:
        tenant_id = tenant_id or settings.tenant_id
        raw = self.redis.get(self._key(tenant_id, host))
        if raw:
            return AssetRecord(**json.loads(raw))
        return AssetRecord(host=host, criticality=Criticality.UNKNOWN)

    def list_all(self, tenant_id: str = None) -> List[AssetRecord]:
        tenant_id = tenant_id or settings.tenant_id
        records = []
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(cursor=cursor, match=f"{ASSET_KEY_PREFIX}{tenant_id}:*", count=100)
            for key in keys:
                raw = self.redis.get(key)
                if raw:
                    records.append(AssetRecord(**json.loads(raw)))
            if cursor == 0:
                break
        return records

    def delete(self, host: str, tenant_id: str = None):
        tenant_id = tenant_id or settings.tenant_id
        self.redis.delete(self._key(tenant_id, host))

    def enrich(self, host: str, tenant_id: str = None) -> dict:
        record = self.get(host, tenant_id=tenant_id)
        return record.model_dump()
