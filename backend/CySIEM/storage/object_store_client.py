"""
Layer 0 — Evidence Lake, cold storage tier.

OpenSearch (opensearch_client.py) is the HOT tier: recent events, fast
query, used by Agent 4 for verification. This module is the COLD tier:
long-term raw log retention, cheap storage, forensic replay.

CLOUD PORTABILITY: this is built on boto3's S3 API, pointed at a local
MinIO instance. MinIO speaks the S3 API natively, so this exact code works
unmodified against real AWS S3, or any other S3-compatible store (Backblaze
B2, Wasabi, Cloudflare R2, Azure via a compatibility shim) - the ONLY thing
that changes to move to cloud is the .env values (endpoint_url, credentials,
bucket region). No code change, no rewrite. That's the whole point of using
boto3 + an S3-compatible endpoint instead of a MinIO-specific SDK.
"""
from __future__ import annotations
import gzip
import json
import logging
from datetime import datetime, timezone
from typing import Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from CySIEM.common.config import settings
from CySIEM.schemas.canonical import CanonicalEvent

logger = logging.getLogger("kksiem.storage.object_store")


class ObjectStoreClient:
    def __init__(self):
        self.bucket = settings.object_store_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.object_store_endpoint_url,
            aws_access_key_id=settings.object_store_access_key,
            aws_secret_access_key=settings.object_store_secret_key,
            config=Config(signature_version="s3v4"),
            region_name=settings.object_store_region,
        )

    def ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            logger.info(f"Creating object store bucket: {self.bucket}")
            self.client.create_bucket(Bucket=self.bucket)

    def _object_key(self, event: CanonicalEvent) -> str:
        # Partitioned by host/date - keeps listing/lookup cheap and mirrors
        # how you'd want this laid out if it were on S3 with lifecycle rules.
        date_prefix = event.event_time.strftime("%Y/%m/%d")
        return f"raw-events/{event.source.host}/{date_prefix}/{event.event_id}.json.gz"

    def archive_event(self, event: CanonicalEvent):
        """Writes the full canonical event (including raw log line) to cold
        storage, gzip-compressed. Called by the normalizer alongside the
        OpenSearch hot-tier write - same event, two tiers, different
        retention/query tradeoffs."""
        key = self._object_key(event)
        body = gzip.compress(event.model_dump_json().encode("utf-8"))
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=body,
                                    ContentType="application/json", ContentEncoding="gzip")
        except ClientError as e:
            logger.error(f"Failed to archive event {event.event_id} to object store: {e}")
            raise

    def fetch_event(self, host: str, event_time: datetime, event_id: str) -> Optional[dict]:
        date_prefix = event_time.strftime("%Y/%m/%d")
        key = f"raw-events/{host}/{date_prefix}/{event_id}.json.gz"
        try:
            resp = self.client.get_object(Bucket=self.bucket, Key=key)
            body = gzip.decompress(resp["Body"].read())
            return json.loads(body)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return None
            raise

    def list_events_for_host_day(self, host: str, date: datetime) -> list[str]:
        prefix = f"raw-events/{host}/{date.strftime('%Y/%m/%d')}/"
        keys = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys

    def health_check(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except Exception as e:
            logger.error(f"Object store health check failed: {e}")
            return False
