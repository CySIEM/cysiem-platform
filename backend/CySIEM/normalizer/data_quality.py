"""
Layer 1 -- Data Fabric: Data Quality.

Pydantic (via RawMessage/CanonicalEvent) already proves an event's JSON
shape is correct - required fields present, types match. It does NOT prove
the data is sensible. A message can be perfectly valid Pydantic and still
contain a malformed IP string, a port number outside 0-65535, a host
claiming a segment that contradicts its own Asset Registry entry, or a
timestamp so implausible it is clearly a parsing bug rather than real
clock skew (timestamp_correction.py handles plausible-but-large skew;
this module catches structurally-impossible timestamps).

Design principle: data quality issues are NOT the same severity as parse
failures. A parse failure (cannot even build a CanonicalEvent) belongs in
DLQ - the event is unusable. A data quality issue means a valid
CanonicalEvent was built, but something about its content is suspect
enough that a human or downstream layer should know, without blocking the
event from being stored and searchable. routing.py treats "quarantine"
(quality-flagged, still indexed, tagged for review) as distinct from
"dlq" (unusable, not indexed).
"""
from __future__ import annotations
import ipaddress
import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger("kksiem.normalizer.data_quality")

MAX_PLAUSIBLE_FUTURE_SECONDS = 3600 * 24 * 7


class QualityIssueCode(str, Enum):
    INVALID_SRC_IP = "invalid_src_ip"
    INVALID_DEST_IP = "invalid_dest_ip"
    INVALID_PORT = "invalid_port"
    SEGMENT_ASSET_MISMATCH = "segment_asset_mismatch"
    IMPLAUSIBLE_TIMESTAMP = "implausible_timestamp"
    UNKNOWN_HOST_IDENTITY = "unknown_host_identity"


class QualityIssue(BaseModel):
    code: QualityIssueCode
    detail: str


class QualityVerdict(BaseModel):
    is_clean: bool
    issues: List[QualityIssue] = []


def _is_valid_ip(value):
    if value is None:
        return True
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _is_valid_port(value):
    if value is None:
        return True
    return 0 <= value <= 65535


def check_data_quality(host, segment, src_ip, dest_ip, src_port, dest_port,
                        event_time, log_type, registered_segment=None,
                        registered_criticality=None):
    issues = []

    if not _is_valid_ip(src_ip):
        issues.append(QualityIssue(code=QualityIssueCode.INVALID_SRC_IP, detail=f"src_ip={src_ip!r} is not a valid IP"))
    if not _is_valid_ip(dest_ip):
        issues.append(QualityIssue(code=QualityIssueCode.INVALID_DEST_IP, detail=f"dest_ip={dest_ip!r} is not a valid IP"))
    if not _is_valid_port(src_port):
        issues.append(QualityIssue(code=QualityIssueCode.INVALID_PORT, detail=f"src_port={src_port!r} out of range"))
    if not _is_valid_port(dest_port):
        issues.append(QualityIssue(code=QualityIssueCode.INVALID_PORT, detail=f"dest_port={dest_port!r} out of range"))

    now = datetime.now(timezone.utc)
    et = event_time if event_time.tzinfo else event_time.replace(tzinfo=timezone.utc)
    if et > now + timedelta(seconds=MAX_PLAUSIBLE_FUTURE_SECONDS):
        issues.append(QualityIssue(
            code=QualityIssueCode.IMPLAUSIBLE_TIMESTAMP,
            detail=f"event_time {et.isoformat()} is more than 7 days in the future"
        ))

    if registered_segment is not None and registered_segment != "unknown" \
            and segment not in ("UNKNOWN", "unknown") and segment != registered_segment:
        issues.append(QualityIssue(
            code=QualityIssueCode.SEGMENT_ASSET_MISMATCH,
            detail=f"event reports segment={segment!r} but Asset Registry has {host!r} as {registered_segment!r}"
        ))

    if registered_criticality is None:
        issues.append(QualityIssue(
            code=QualityIssueCode.UNKNOWN_HOST_IDENTITY,
            detail=f"host={host!r} is not registered in the Asset Registry"
        ))

    verdict = QualityVerdict(is_clean=(len(issues) == 0), issues=issues)
    if not verdict.is_clean:
        logger.warning(f"Data quality issues for host={host}: {[i.code for i in issues]}")
    return verdict