"""
Layer 1 -- Data Fabric: Timestamp Correction.

v4.1's Data Fabric spec requires "Timestamp Correction" as a first-class
concern. This matters because every downstream layer -- Layer 5
Correlation (timeline building, attack chain reconstruction), Layer 6
Investigation (event ordering), Agent 4's historical-baseline queries --
assumes event_time is trustworthy and comparable across hosts. It usually
isn't, for two independent reasons this module addresses separately:

1. CLOCK SKEW: a source host's own clock can be wrong (NTP not configured,
   VM clock drift after a snapshot restore -- your own earlier Windows
   Server test literally generated a "system time was changed" event,
   event code 4616, which is exactly this failure mode in the wild).
   We compare the source-reported timestamp against KKSIEM's own ingestion
   time and flag/quantify the drift per host.

2. INGESTION LAG: normal network/processing delay between when an event
   happened and when the normalizer sees it. This is expected and NOT an
   error -- only large lag (minutes+) is worth flagging, since a collector
   that batches/retries after an outage can legitimately deliver events
   late.

Correction policy (deliberately conservative for a security tool): we
NEVER silently rewrite event_time to "fix" it -- an event's original
reported time is forensic evidence and altering it would be a serious
integrity problem if this system is ever used in an investigation with
legal/compliance weight. Instead we:
  - preserve the original source-reported time in event_time (unchanged)
  - stamp a UTC-normalized, monotonic ingested_at (already existed)
  - compute and attach skew_seconds + a quality verdict into
    extensions.timestamp_quality, so Layer 5 correlation can choose to
    down-weight or exclude events with untrustworthy timestamps, with the
    original data fully intact for audit.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger("kksiem.normalizer.timestamp_correction")

SKEW_WARN_SECONDS = 60
SKEW_SUSPECT_SECONDS = 300
SKEW_REJECT_SECONDS = 86400


class TimestampQualityVerdict(str, Enum):
    OK = "ok"
    WARN = "warn"
    SUSPECT = "suspect"
    REJECT_CANDIDATE = "reject_candidate"


class TimestampQuality(BaseModel):
    source_reported_time: str
    ingested_at: str
    skew_seconds: float
    verdict: TimestampQualityVerdict
    host_rolling_skew_seconds: Optional[float] = None


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def classify_skew(skew_seconds: float) -> TimestampQualityVerdict:
    abs_skew = abs(skew_seconds)
    if abs_skew >= SKEW_REJECT_SECONDS:
        return TimestampQualityVerdict.REJECT_CANDIDATE
    if abs_skew >= SKEW_SUSPECT_SECONDS:
        return TimestampQualityVerdict.SUSPECT
    if abs_skew >= SKEW_WARN_SECONDS:
        return TimestampQualityVerdict.WARN
    return TimestampQualityVerdict.OK


def evaluate_timestamp(source_reported_time: datetime, ingested_at: datetime,
                        host_rolling_skew_seconds: Optional[float] = None) -> TimestampQuality:
    source_utc = ensure_utc(source_reported_time)
    ingest_utc = ensure_utc(ingested_at)
    skew = (ingest_utc - source_utc).total_seconds()
    verdict = classify_skew(skew)

    if verdict != TimestampQualityVerdict.OK:
        logger.warning(
            f"Timestamp skew detected: source={source_utc.isoformat()} "
            f"ingested={ingest_utc.isoformat()} skew={skew:.1f}s verdict={verdict}"
        )

    return TimestampQuality(
        source_reported_time=source_utc.isoformat(),
        ingested_at=ingest_utc.isoformat(),
        skew_seconds=round(skew, 3),
        verdict=verdict,
        host_rolling_skew_seconds=host_rolling_skew_seconds,
    )