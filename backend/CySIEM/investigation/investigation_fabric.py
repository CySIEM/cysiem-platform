"""
Layer 6 -- Investigation Fabric.

v1 originally had Agent 4 querying OpenSearch directly, inline in its own
module. This formalizes that into a standalone Investigation Fabric service
- the same queries Agent 4 needs (host timeline, related hosts, asset
context) but as a reusable interface, not logic embedded in one agent.

Why this matters for the v4.1 path: Layer 8 (Security Copilot) and Layer 9
(Human Review) will both want to run these same "investigate this host"
queries interactively, not just as part of Agent 4's automated flow. Having
them here means Copilot/human tooling calls this module directly later,
rather than needing to extract logic out of Agent 4's prompt-building code.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from pydantic import BaseModel
from CySIEM.storage.opensearch_client import OpenSearchClient
from CySIEM.intelligence.asset_registry import AssetRegistry, AssetRecord

opensearch = OpenSearchClient()
assets = AssetRegistry()


class HostInvestigationReport(BaseModel):
    host: str
    asset: AssetRecord
    lookback_hours: int
    event_count: int
    events: List[dict]
    category_breakdown: Dict[str, int]
    distinct_users: List[str]
    distinct_src_ips: List[str]


def investigate_host(host: str, lookback_hours: int = 24, max_events: int = 200) -> HostInvestigationReport:
    """The core Investigation Fabric operation: pull everything known about
    a host in a time window, plus its business context. This is what
    Agent 4 calls today, and what a human analyst or Layer 8 Copilot would
    call interactively later - same function, different caller."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=lookback_hours)

    events = opensearch.query_host_history(host, start, now, size=max_events)
    asset = assets.get(host)

    category_breakdown: Dict[str, int] = {}
    users = set()
    src_ips = set()
    for e in events:
        norm = e.get("normalized", {})
        cat = norm.get("event_category", "other")
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
        if norm.get("user"):
            users.add(norm["user"])
        if norm.get("src_ip"):
            src_ips.add(norm["src_ip"])

    return HostInvestigationReport(
        host=host,
        asset=asset,
        lookback_hours=lookback_hours,
        event_count=len(events),
        events=events,
        category_breakdown=category_breakdown,
        distinct_users=sorted(users),
        distinct_src_ips=sorted(src_ips),
    )


def find_related_hosts(host: str, lookback_hours: int = 24) -> List[str]:
    """Finds other hosts that appear as src_ip/dest_ip in this host's event
    history - a minimal stand-in for what Layer 3B (Security Graph) will do
    properly later via real entity relationships. This version is a
    same-window IP co-occurrence scan against OpenSearch, not a graph
    traversal - honestly basic, but enough to answer 'what else was this
    host talking to' today."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=lookback_hours)
    events = opensearch.query_host_history(host, start, now, size=200)

    related_ips = set()
    for e in events:
        norm = e.get("normalized", {})
        for ip_field in ("src_ip", "dest_ip"):
            ip = norm.get(ip_field)
            if ip and ip != e.get("source", {}).get("ip"):
                related_ips.add(ip)
    return sorted(related_ips)
