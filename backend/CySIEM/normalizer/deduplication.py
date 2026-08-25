"""
Layer 1 -- Data Fabric: Deduplication.

Real risk, not theoretical: our collector deploy scripts configure
Restart=always (Fluent Bit) and sc.exe failure ... restart (Winlogbeat)
specifically so a crashed collector recovers automatically. But a crash
mid-flush, or a Kafka producer retry after a transient network blip, can
legitimately re-send an event that already made it through. Undetected,
duplicates inflate event counts, skew Agent 2's window-based analysis,
and corrupt Layer 5 correlation confidence scoring.

Approach: content-hash based idempotency, backed by Redis (the same
instance already required for Agent 3's correlation store and the Asset
Registry - no new infrastructure). We hash host + log_type + raw content
ONLY.

IMPORTANT (found and fixed via integration testing, not assumed correct):
the hash deliberately does NOT include any timestamp field. RawMessage's
received_at is stamped fresh via default_factory on every construction,
including on a genuine retry of the identical underlying event - including
it in the hash silently defeats deduplication entirely, since a retry
would never hash identically to the original delivery. The raw content
itself already carries the event's real identity, including any timestamp
the source system embedded in it.

MULTI-TENANCY (this revision): tenant_id is now part of both the hash and
the Redis key. Previously the hash was host+log_type+raw only - two
different tenants whose collectors happen to produce byte-identical raw
content for a coincidentally-identically-named host would collide, and one
tenant's legitimate event would be silently dropped as a "duplicate" of a
different tenant's event. tenant_id in the key makes this structurally
impossible.

TTL on the dedup keys (not permanent storage) is deliberate: an identical
raw log line recurring days apart (e.g. a recurring cron job's output) is
a legitimate distinct event, not a duplicate delivery. The dedup window
only needs to cover realistic retry/restart timeframes.
"""
from __future__ import annotations
import hashlib
import logging
from typing import Tuple
import redis
from CySIEM.common.config import settings

logger = logging.getLogger("kksiem.normalizer.dedup")

DEDUP_KEY_PREFIX = "kksiem:dedup:"
PROCESSING_SUFFIX = ":processing"



class DeduplicationStore:
    def __init__(self, ttl_seconds=None):
        self.ttl_seconds = (
            ttl_seconds or settings.dedup_window_seconds
        )

        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )

    def _compute_hash(
        self,
        tenant_id,
        host,
        log_type,
        raw,
    ):
        material = (
            f"{tenant_id}|{host}|{log_type}|{raw}"
        ).encode("utf-8")

        return hashlib.sha256(material).hexdigest()

    def _processed_key(
        self,
        tenant_id,
        content_hash,
    ):
        return (
            f"{DEDUP_KEY_PREFIX}"
            f"{tenant_id}:{content_hash}"
        )

    def _processing_key(
        self,
        tenant_id,
        content_hash,
    ):
        return (
            f"{self._processed_key(tenant_id, content_hash)}"
            f"{PROCESSING_SUFFIX}"
        )

    def acquire(
        self,
        tenant_id,
        host,
        log_type,
        raw,
    ):
        content_hash = self._compute_hash(
            tenant_id,
            host,
            log_type,
            raw,
        )

        processed_key = self._processed_key(
            tenant_id,
            content_hash,
        )

        if self.redis.exists(processed_key):
            return False, content_hash

        processing_key = self._processing_key(
            tenant_id,
            content_hash,
        )

        acquired = self.redis.set(
            processing_key,
            "1",
            nx=True,
            ex=300,
        )

        return bool(acquired), content_hash

    def mark_processed(
        self,
        tenant_id,
        content_hash,
    ):
        processed_key = self._processed_key(
            tenant_id,
            content_hash,
        )

        processing_key = self._processing_key(
            tenant_id,
            content_hash,
        )

        pipe = self.redis.pipeline()

        pipe.set(
            processed_key,
            "1",
            ex=self.ttl_seconds,
        )

        pipe.delete(processing_key)

        pipe.execute()

    def release(
        self,
        tenant_id,
        content_hash,
    ):
        processing_key = self._processing_key(
            tenant_id,
            content_hash,
        )

        self.redis.delete(processing_key)

    # Backward-compatible method.
    def check_and_mark(
        self,
        tenant_id,
        host,
        log_type,
        raw,
    ):
        acquired, content_hash = self.acquire(
            tenant_id,
            host,
            log_type,
            raw,
        )

        if not acquired:
            return True, content_hash

        self.mark_processed(
            tenant_id,
            content_hash,
        )

        return False, content_hash

    def health_check(self):
        try:
            return bool(self.redis.ping())
        except Exception as e:
            logger.error(
                f"Dedup store health check failed: {e}"
            )
            return False







































# class DeduplicationStore:
#     def __init__(self, ttl_seconds=None):
#         self.ttl_seconds = ttl_seconds or settings.dedup_window_seconds
#         self.redis = redis.Redis(
#             host=settings.redis_host, port=settings.redis_port, db=settings.redis_db,
#             decode_responses=True,
#         )

#     def _compute_hash(self, tenant_id, host, log_type, raw):
#         material = f"{tenant_id}|{host}|{log_type}|{raw}".encode("utf-8")
#         return hashlib.sha256(material).hexdigest()

#     def check_and_mark(self, tenant_id, host, log_type, raw):
#         """Returns (is_duplicate, content_hash). Atomic via Redis SET NX,
#         so two near-simultaneous deliveries of the same content can't both
#         be judged 'not a duplicate' in a race. tenant_id is REQUIRED so a
#         caller can never accidentally check/mark a fingerprint in the
#         wrong tenant's namespace by omission."""
#         content_hash = self._compute_hash(tenant_id, host, log_type, raw)
#         key = f"{DEDUP_KEY_PREFIX}{tenant_id}:{content_hash}"

#         was_new = self.redis.set(key, "1", nx=True, ex=self.ttl_seconds)
#         is_duplicate = not bool(was_new)

#         if is_duplicate:
#             logger.info(f"Duplicate detected: tenant={tenant_id} host={host} log_type={log_type} hash={content_hash[:12]}...")

#         return is_duplicate, content_hash

#     def health_check(self):
#         try:
#             return bool(self.redis.ping())
#         except Exception as e:
#             logger.error(f"Dedup store health check failed: {e}")
#             return False