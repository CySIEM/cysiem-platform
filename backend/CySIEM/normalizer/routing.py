"""
Layer 1 -- Data Fabric: Routing.

This is the single decision point that ties together deduplication.py's
is_duplicate flag, data_quality.py's QualityVerdict, and
timestamp_correction.py's TimestampQuality into one routing outcome.

Routing outcomes, in priority order (first match wins):
  1. DUPLICATE   - drop silently (not an error, not a quality issue - just
                    a re-delivery of something already ingested).
  2. QUARANTINE  - successfully parsed, but data_quality.py or
                    timestamp_correction.py flagged something suspect.
                    Still indexed (searchable, not lost) but written to a
                    SEPARATE index/topic so quarantined events don't
                    silently dilute the confidence of clean data feeding
                    Agent 2 and Sigma rules.
  3. CLEAN       - normal path, exactly what v1 always did.

(DLQ is handled entirely upstream of this module - events that fail to
parse never become a CanonicalEvent at all, see service.py's dead_letter()
path - this module is never reached for those.)
"""
from __future__ import annotations
import logging
from enum import Enum
from pydantic import BaseModel
from CySIEM.normalizer.data_quality import QualityVerdict
from CySIEM.normalizer.timestamp_correction import TimestampQuality, TimestampQualityVerdict

logger = logging.getLogger("kksiem.normalizer.routing")


class RouteDecision(str, Enum):
    DUPLICATE = "duplicate"
    QUARANTINE = "quarantine"
    CLEAN = "clean"


class RoutingResult(BaseModel):
    decision: RouteDecision
    reasons: list[str] = []


def decide_route(is_duplicate: bool, quality: QualityVerdict, timestamp_quality: TimestampQuality) -> RoutingResult:
    if is_duplicate:
        return RoutingResult(decision=RouteDecision.DUPLICATE, reasons=["content hash matched a recent delivery"])

    reasons = []
    if not quality.is_clean:
        reasons.extend(f"data_quality:{issue.code.value}" for issue in quality.issues)

    if timestamp_quality.verdict in (TimestampQualityVerdict.SUSPECT, TimestampQualityVerdict.REJECT_CANDIDATE):
        reasons.append(f"timestamp_quality:{timestamp_quality.verdict.value}")

    if reasons:
        return RoutingResult(decision=RouteDecision.QUARANTINE, reasons=reasons)

    return RoutingResult(decision=RouteDecision.CLEAN, reasons=[])