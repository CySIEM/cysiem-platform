"""
Layer 1 (Data Fabric) + Layer 2 (Canonical Schema) Normalizer Service.

Consumes from {tenant}.raw.windows / {tenant}.raw.linux / {tenant}.raw.firewall,
and for every message:
  1. Deduplication check (Layer 1) - drop silently if this exact content
     was already ingested within the dedup window (collector retry/restart)
  2. Parse + build CanonicalEvent (Layer 2 - unchanged from v1)
  3. Layer 2A Asset Intelligence enrichment (unchanged from v1)
  4. Timestamp Correction (Layer 1) - evaluate skew between the SOURCE's
     own timestamp and ingestion time, attach verdict, NEVER rewrite the
     original event_time (forensic integrity)
  5. Data Quality validation (Layer 1) - semantic checks beyond schema shape
  6. Routing decision (Layer 1) - combines dedup+quality+timestamp verdicts
     into CLEAN / QUARANTINE / DUPLICATE, and indexes accordingly:
       CLEAN      -> normal hot-tier index + normalized.events (Path B) + cold tier
       QUARANTINE -> separate quarantine index, tagged, NOT forwarded to
                     Agent 2 (Path B) so flagged data doesn't dilute AI
                     analysis confidence, but fully visible to a human
                     reviewer or Agent 4's historical queries
       DUPLICATE  -> not indexed anywhere, debug-logged only

MULTI-TENANCY (this revision): every producer/consumer topic now goes
through settings.topic(...) instead of the bare settings.topic_* string,
so this normalizer only ever consumes/produces within its own tenant's
namespace. Unknown-tenant messages are routed straight to DLQ with a clear
reason rather than crashing or being silently processed.

TIMESTAMP CORRECTION (this revision): previously event_time=raw_msg.
received_at was used for BOTH the CanonicalEvent's event_time AND as the
"source reported time" input to evaluate_timestamp() - meaning skew was
computed by comparing ingestion time against itself, always returning ~0
regardless of real source clock skew. This now uses raw_msg.event_time
(the source-native timestamp, when the collector could determine one) for
both the canonical event's event_time and the skew comparison, falling
back to received_at only when the collector genuinely couldn't supply a
source timestamp (flagged explicitly via used_fallback_timestamp).

Run standalone with: python -m kksiem.normalizer.service
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from CySIEM.common.config import settings
from CySIEM.common.kafka_client import KafkaProducerClient, KafkaConsumerClient
from CySIEM.schemas.canonical import CanonicalEvent, RawMessage, SourceInfo, Segment, SourceType
from CySIEM.normalizer.parsers import parse
from CySIEM.normalizer.deduplication import DeduplicationStore
from CySIEM.normalizer.timestamp_correction import evaluate_timestamp
from CySIEM.normalizer.data_quality import check_data_quality
from CySIEM.normalizer.routing import decide_route, RouteDecision
from CySIEM.storage.opensearch_client import OpenSearchClient
from CySIEM.storage.object_store_client import ObjectStoreClient
from CySIEM.normalizer.batch_export import BatchExporter
from CySIEM.intelligence.asset_registry import AssetRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kksiem.normalizer")

# tenant_ids this normalizer instance will accept. Single-install
# deployment model: always exactly {settings.tenant_id}. Expressed as a
# set (not an equality check) so a future multi-tenant deployment can
# widen this without changing the validation logic itself.
KNOWN_TENANTS = {settings.tenant_id}


class ValidationFailure(Exception):
    """A RawMessage that parsed (pydantic-valid) but fails a semantic
    check before it's trusted as real ingestable data (unknown tenant).
    Distinct from a parse failure - this is a config problem on an
    endpoint, not a code bug."""
    pass


def resolve_segment(ip):
    if not ip:
        return Segment.UNKNOWN
    for prefix, seg in settings.known_segments.items():
        if ip.startswith(prefix):
            try:
                return Segment(seg)
            except ValueError:
                return Segment.UNKNOWN
    return Segment.UNKNOWN


class NormalizerService:
    def __init__(self):
        self.producer = KafkaProducerClient(
            settings.kafka_bootstrap_servers, client_id="kksiem-normalizer"
        )
        self.consumer = KafkaConsumerClient(
            settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group_normalizer,
            topics=[
                settings.topic(settings.topic_raw_windows),
                settings.topic(settings.topic_raw_linux),
                settings.topic(settings.topic_raw_firewall),
            ],
        )
        self.opensearch = OpenSearchClient()
        self.object_store = ObjectStoreClient()
        self.assets = AssetRegistry()
        self.dedup = DeduplicationStore()
        self.batch_exporter: BatchExporter | None = None
        if not self.dedup.health_check():
            raise RuntimeError(
                "Normalizer requires Redis for deduplication - cannot start without it. "
                "Check REDIS_HOST/REDIS_PORT."
            )

        
        if settings.batch_export_enabled:
            self.batch_exporter = BatchExporter(
                output_dir=settings.batch_export_output_dir,
                tenant_id=settings.tenant_id,
                window_seconds=settings.batch_export_window_seconds,
            )
            logger.info(
                f"Batch export enabled: dir={settings.batch_export_output_dir} "
                f"window={settings.batch_export_window_seconds}s"
            )

    def _validate_tenant(self, raw_msg: RawMessage) -> None:
        if raw_msg.tenant_id not in KNOWN_TENANTS:
            raise ValidationFailure(
                f"Unknown tenant_id={raw_msg.tenant_id!r}; this normalizer "
                f"instance serves {KNOWN_TENANTS}. Check the collector's "
                f"TENANT_ID configuration on host={raw_msg.host!r}."
            )

    def handle_message(self, parsed, key):
        raw_msg = RawMessage(**parsed)

        # --------------------------------------------------
        # 1. Validate tenant
        # --------------------------------------------------
        try:
            self._validate_tenant(raw_msg)

        except ValidationFailure as e:
            self.producer.send(
                topic=settings.topic(settings.topic_dlq),
                value={
                    "error": str(e),
                    "raw_message": raw_msg.model_dump(mode="json"),
                },
            )

            logger.error(str(e))
            return

        # --------------------------------------------------
        # 2. Acquire temporary deduplication processing lock
        # --------------------------------------------------
        acquired, content_hash = self.dedup.acquire(
            tenant_id=raw_msg.tenant_id,
            host=raw_msg.host,
            log_type=raw_msg.log_type,
            raw=raw_msg.raw,
        )

        # Event was already processed OR is currently
        # being processed by another worker.
        if not acquired:
            logger.debug(
                "Duplicate or currently-processing event skipped "
                "tenant=%s host=%s hash=%s",
                raw_msg.tenant_id,
                raw_msg.host,
                content_hash[:12],
            )
            return

        # --------------------------------------------------
        # 3. Process the event
        #
        # If ANYTHING below fails:
        # - release dedup processing lock
        # - raise the error
        # - Kafka consumer/error handler decides what happens
        # --------------------------------------------------
        try:

            # ----------------------------------------------
            # Resolve segment safely
            # ----------------------------------------------
            if raw_msg.segment:
                try:
                    segment = Segment(raw_msg.segment)

                except ValueError:
                    logger.warning(
                        "Unknown segment=%r for host=%s. "
                        "Falling back to IP-based segment resolution.",
                        raw_msg.segment,
                        raw_msg.host,
                    )

                    segment = resolve_segment(raw_msg.ip)

            else:
                segment = resolve_segment(raw_msg.ip)

            # ----------------------------------------------
            # Resolve source type safely
            # ----------------------------------------------
            source_type = (
                SourceType(raw_msg.source_type)
                if raw_msg.source_type
                in [e.value for e in SourceType]
                else SourceType.UNKNOWN
            )

            # ----------------------------------------------
            # Parse the raw log
            # ----------------------------------------------
            normalized_fields = parse(
                raw_msg.log_type,
                raw_msg.raw,
            )

            # ----------------------------------------------
            # Asset enrichment
            # ----------------------------------------------
            asset_context = self.assets.enrich(
                raw_msg.host,
                tenant_id=raw_msg.tenant_id,
            )

            registered_segment = asset_context.get("segment")
            registered_criticality = asset_context.get(
                "criticality"
            )

            if registered_criticality == "unknown":
                registered_criticality = None

            # ----------------------------------------------
            # Timestamp handling
            # ----------------------------------------------
            # Prefer collector-provided event time.
            # Fall back to received_at only if event_time
            # was not supplied.
            used_fallback_timestamp = (
                raw_msg.event_time is None
            )

            source_reported_time = (
                raw_msg.event_time
                or raw_msg.received_at
            )

            ingested_at = datetime.now(timezone.utc)

            timestamp_quality = evaluate_timestamp(
                source_reported_time,
                ingested_at,
            )

            # ----------------------------------------------
            # Create canonical event
            # ----------------------------------------------
            event = CanonicalEvent(
                event_time=source_reported_time,

                source=SourceInfo(
                    tenant_id=raw_msg.tenant_id,
                    host=raw_msg.host,
                    ip=raw_msg.ip,
                    segment=segment,
                    source_type=source_type,
                    log_type=raw_msg.log_type,
                    collector=raw_msg.collector,
                ),

                normalized=normalized_fields,

                raw=raw_msg.raw,

                raw_format=raw_msg.raw_format,

                extensions={
                    "asset": asset_context,

                    "timestamp_quality": {
                        **timestamp_quality.model_dump(
                            mode="json"
                        ),

                        "used_fallback_timestamp":
                            used_fallback_timestamp,
                    },
                },
            )

            # ----------------------------------------------
            # Data quality validation
            # ----------------------------------------------
            quality = check_data_quality(
                host=raw_msg.host,

                segment=segment.value,

                src_ip=normalized_fields.src_ip,

                dest_ip=normalized_fields.dest_ip,

                src_port=normalized_fields.src_port,

                dest_port=normalized_fields.dest_port,

                event_time=event.event_time,

                log_type=raw_msg.log_type,

                registered_segment=registered_segment,

                registered_criticality=
                    registered_criticality,
            )

            event.extensions["data_quality"] = (
                quality.model_dump(mode="json")
            )

            # ----------------------------------------------
            # Decide CLEAN or QUARANTINE
            # ----------------------------------------------
            route = decide_route(
                is_duplicate=False,
                quality=quality,
                timestamp_quality=timestamp_quality,
            )

            event.extensions["routing"] = (
                route.model_dump(mode="json")
            )

            # ----------------------------------------------
            # Write the event
            # ----------------------------------------------
            if route.decision == RouteDecision.CLEAN:

                self._write_clean(event)

            elif route.decision == RouteDecision.QUARANTINE:

                self._write_quarantine(
                    event,
                    route.reasons,
                )

            else:
                # This protects against future route types
                # being added without handling them here.
                raise RuntimeError(
                    f"Unhandled routing decision: "
                    f"{route.decision}"
                )

            # ----------------------------------------------
            # IMPORTANT:
            #
            # Only mark the event as processed AFTER
            # parsing, enrichment, validation, routing,
            # and Kafka output all succeed.
            # ----------------------------------------------
            self.dedup.mark_processed(
                tenant_id=raw_msg.tenant_id,
                content_hash=content_hash,
            )

            logger.debug(
                "Successfully normalized event "
                "tenant=%s host=%s "
                "source_type=%s log_type=%s "
                "route=%s hash=%s",
                raw_msg.tenant_id,
                raw_msg.host,
                source_type.value,
                raw_msg.log_type,
                route.decision.value,
                content_hash[:12],
            )

        # --------------------------------------------------
        # 4. Something failed
        # --------------------------------------------------
        except Exception:

            # Remove temporary processing lock.
            #
            # This is important because otherwise the event
            # could remain permanently marked as "processing".
            self.dedup.release(
                tenant_id=raw_msg.tenant_id,
                content_hash=content_hash,
            )

            logger.exception(
                "Failed to normalize event "
                "tenant=%s host=%s "
                "source_type=%s log_type=%s",
                raw_msg.tenant_id,
                raw_msg.host,
                raw_msg.source_type,
                raw_msg.log_type,
            )

            # VERY IMPORTANT:
            #
            # Do not swallow this exception.
            # Let the Kafka consumer know processing failed.
            raise



    def _write_clean(self, event):
        self.producer.send_and_wait(
            topic=settings.topic(
                settings.topic_normalized,
                tenant_id=event.source.tenant_id,
            ),
            value=event,
            key=event.source.host,
        )
        self.opensearch.index_event(event)
        try:
            self.object_store.archive_event(event)
        except Exception as e:
            logger.error(f"Cold-tier archive failed for event {event.event_id} (non-fatal): {e}")
        logger.info(
            f"Normalized (clean) {event.event_id} tenant={event.source.tenant_id} "
            f"host={event.source.host} segment={event.source.segment} "
            f"category={event.normalized.event_category}"
        )

    def _write_quarantine(self, event, reasons):
        self.opensearch.index_event(event, index_prefix=settings.opensearch_quarantine_index_prefix)
        self.producer.send_and_wait(
            topic=settings.topic(
                settings.topic_quarantine,
                tenant_id=event.source.tenant_id,
            ),
            value=event,
            key=event.source.host,
        )
        try:
            self.object_store.archive_event(event)
        except Exception as e:
            logger.error(f"Cold-tier archive failed for quarantined event {event.event_id} (non-fatal): {e}")
        logger.warning(f"Quarantined {event.event_id} tenant={event.source.tenant_id} host={event.source.host} reasons={reasons}")

    def dead_letter(self, error, raw_bytes):
        self.producer.send(
            topic=settings.topic(settings.topic_dlq),
            value={"error": str(error), "raw": raw_bytes.decode("utf-8", errors="replace")},
        )

    def run(self):
        logger.info(f"Normalizer service starting for tenant={settings.tenant_id} (Layer 1 + Layer 2 pipeline)...")
        self.opensearch.ensure_index_template()
        self.object_store.ensure_bucket()        
        try:
            self.consumer.poll_loop(self.handle_message, on_error=self.dead_letter)
        finally:
            # Flush whatever's buffered in the in-progress batch-export
            # window so a clean shutdown never silently drops up to
            # window_seconds of already-normalized events. No-op when
            # batch export is disabled.
            if self.batch_exporter is not None:
                self.batch_exporter.close()



if __name__ == "__main__":
    NormalizerService().run()
