"""
Canonical Security Schema (Layer 2).

Every raw log, regardless of source (pfSense, Windows, Linux), is normalized
into this shape before it is written to the `normalized.events` Kafka topic
or indexed in OpenSearch. This is the single contract that lets Agent 1,
Agent 2, Agent 3, and Agent 4 all reason about "which host did this event
come from" without ambiguity - source identity is a first-class field on
every event, not something inferred later from topic name or log format.

SCHEMA VERSIONING (KKSIEM v1 -> v4.1 migration path):
Every CanonicalEvent carries `schema_version`. Consumers declare which
versions they support rather than assuming the current shape. This is what
lets v4.1's Layer 2A (Asset Intelligence) and Layer 3B (Security Graph)
attach NEW fields later without breaking v1 consumers that only know the
v1.0 shape - old consumers keep working on old-shaped events, new consumers
can require v1.1+ and get the new fields. The `extensions` dict on
CanonicalEvent exists specifically as the landing zone for these future
fields (asset criticality, graph node IDs, etc) so the core schema doesn't
need a breaking change when v4.1 layers are added - only an additive one.

MULTI-TENANCY (this revision): source.tenant_id is now REQUIRED. Every
Kafka topic name and OpenSearch index name is namespaced by this value
(see config.py's settings.topic() and CanonicalEvent.index_name below), so
a missing/wrong tenant_id fails structurally (wrong topic, wrong index)
rather than leaking across tenants via a forgotten filter. Single-install
deployments always use one fixed tenant_id (config.py's settings.tenant_id,
default "default") - this is deployment-model-agnostic groundwork for a
future multi-tenant SaaS path, not something you need to manage day to day.

TIMESTAMP CORRECTION (this revision): RawMessage.event_time added.
Previously RawMessage only had `received_at` (ingestion time), and the
normalizer was passing that value into BOTH CanonicalEvent.event_time AND
timestamp_correction.py's "source reported time" argument - meaning skew
was always computed against itself and could never be nonzero. Collectors
that CAN determine the source's own timestamp (winlogbeat's @timestamp,
fluent-bit's parsed syslog time) should populate this; when they can't, it
stays None and the normalizer explicitly falls back to received_at,
flagging that fallback rather than silently treating ingestion time as if
it were a real source timestamp.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator

# Current schema version this codebase produces. Bump the MINOR version for
# additive changes (new optional fields), MAJOR for breaking changes.
CURRENT_SCHEMA_VERSION = "1.1"

# Versions this codebase's consumers (normalizer, agents) can read.
# 1.1 adds: source.tenant_id (required), RawMessage.event_time (optional,
# source-native timestamp). v1.0 events lack tenant_id - callers migrating
# historical v1.0 data must backfill a tenant_id before re-reading it as v1.1.
SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1"}


class SchemaVersionError(ValueError):
    """Raised when a consumer receives an event whose schema_version it
    does not know how to handle. Callers should route these to a DLQ /
    quarantine topic rather than guessing at the shape."""
    pass


def assert_supported_version(schema_version: str, supported=None):
    supported = supported or SUPPORTED_SCHEMA_VERSIONS
    if schema_version not in supported:
        raise SchemaVersionError(
            f"Event schema_version={schema_version!r} not in supported set {supported}. "
            f"This consumer needs updating, or the event needs migrating."
        )


class SourceType(str, Enum):
    WINDOWS_SERVER = "windows_server"
    WINDOWS_CLIENT = "windows_client"
    LINUX_SERVER = "linux_server"
    FIREWALL = "firewall"
    UNKNOWN = "unknown"


class Segment(str, Enum):
    LAN = "LAN"
    OPT1 = "OPT1"   # User workstations
    OPT2 = "OPT2"   # Server network
    OPT3 = "OPT3"   # Attack network (Kali)
    OPT4 = "OPT4"   # KKSIEM network
    UNKNOWN = "UNKNOWN"


class EventCategory(str, Enum):
    AUTHENTICATION = "authentication"
    PROCESS = "process"
    NETWORK = "network"
    FILE = "file"
    FIREWALL_TRAFFIC = "firewall_traffic"
    DNS = "dns"
    SYSTEM = "system"
    OTHER = "other"


class SourceInfo(BaseModel):
    """Identity of the machine/device that produced this log. This is the
    field set that solves 'which endpoint did this come from' for every
    consumer downstream, forever."""
    tenant_id: str = Field(..., description="Owning tenant/customer. Every "
        "Kafka topic and OpenSearch index is namespaced by this value.")
    host: str = Field(..., description="Hostname, e.g. WIN-SRV01")
    ip: Optional[str] = Field(None, description="Source IP at time of log")
    segment: Segment = Field(Segment.UNKNOWN, description="Network segment / OPT")
    source_type: SourceType = Field(SourceType.UNKNOWN)
    log_type: str = Field(..., description="e.g. security_eventlog, auditd, pfsense_filterlog, sysmon")
    collector: str = Field(..., description="Which shipper produced this: winlogbeat | fluent-bit")


class NormalizedFields(BaseModel):
    """Best-effort extracted fields, mapped toward OCSF-style naming.
    Not every field will be populated for every log type - that's expected."""
    event_category: EventCategory = EventCategory.OTHER
    action: Optional[str] = None            # e.g. logon_failed, process_created, conn_blocked
    user: Optional[str] = None
    process_name: Optional[str] = None
    parent_process: Optional[str] = None
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dest_ip: Optional[str] = None
    dest_port: Optional[int] = None
    protocol: Optional[str] = None
    outcome: Optional[str] = None           # success | failure | unknown
    message: Optional[str] = None           # short human-readable summary


class CanonicalEvent(BaseModel):
    """The full envelope. This is what gets written to Kafka `normalized.events`
    and indexed into OpenSearch. Agents consume this shape directly."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_time: datetime = Field(..., description="Original timestamp from the source log")

    source: SourceInfo
    normalized: NormalizedFields
    ocsf_class: Optional[str] = Field(None, description="OCSF class name reference, e.g. 'Authentication'")

    raw: str = Field(..., description="Original untouched log line, preserved for forensic replay")
    raw_format: str = Field(..., description="syslog | winevent_xml | json | auditd")

    schema_version: str = CURRENT_SCHEMA_VERSION

    # Forward-compatible landing zone for v4.1 layers that don't exist yet
    # (Layer 2A Asset Intelligence -> extensions["asset"], Layer 3B Security
    # Graph -> extensions["graph_node_id"], etc). Old (v1) consumers ignore
    # this dict entirely and keep working unmodified. New consumers can read
    # specific keys once populated, without a schema migration.
    extensions: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_time", mode="before")
    @classmethod
    def ensure_tz(cls, v):
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if isinstance(v, datetime) and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    def to_opensearch_doc(self) -> Dict[str, Any]:
        doc = self.model_dump(mode="json")
        return doc

    def index_name(self, prefix: str) -> str:
        """Tenant-namespaced daily index, e.g. kksiem-events-default-2026.07.29.
        Tenant sits in the index NAME (not just as a filterable field) so a
        query that forgets a tenant filter still cannot physically read
        another tenant's documents."""
        return f"{prefix}-{self.source.tenant_id}-{self.event_time.strftime('%Y.%m.%d')}"


class RawMessage(BaseModel):
    """What lands on the raw.* Kafka topics, before normalization.
    Collectors are only required to produce this much - minimal tagging
    at the shipper level, full canonicalization happens in the normalizer."""
    tenant_id: str
    host: str
    ip: Optional[str] = None
    segment: Optional[str] = None
    source_type: Optional[str] = None
    log_type: str
    collector: str
    raw: str
    raw_format: str = "syslog"

    # Original timestamp as parsed by the collector FROM THE SOURCE LOG
    # ITSELF (winlogbeat's @timestamp, fluent-bit's parsed syslog time,
    # etc) - NOT when KKSIEM received the message. Optional because not
    # every raw format guarantees a parseable source timestamp; when
    # absent, the normalizer falls back to received_at and flags it
    # explicitly rather than silently treating ingestion time as if it
    # were the source time.
    event_time: Optional[datetime] = None

    # When KKSIEM's collector actually shipped this. Always present - used
    # as the event_time fallback AND as the "ingested_at" side of the skew
    # comparison in timestamp_correction.evaluate_timestamp.
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("event_time", mode="before")
    @classmethod
    def parse_event_time(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v
