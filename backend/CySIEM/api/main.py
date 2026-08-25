"""
Minimal status/query API for KKSIEM. Run with: python run.py api
GET  /health               - liveness check (also checks Redis + OpenSearch)
GET  /events/{host}        - recent events for a host (Evidence Lake query)
GET  /alerts                - recent confirmed alerts
POST /verdicts              - analyst submits a verdict on an alert (Layer 9 -> Layer 11 bridge)
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Query
from CySIEM.storage.opensearch_client import OpenSearchClient
from CySIEM.common.config import settings
from CySIEM.common.kafka_client import KafkaProducerClient
from CySIEM.schemas.agent_io import HumanVerdict
from CySIEM.agents.correlation_store import CorrelationStore
from CySIEM.intelligence.asset_registry import AssetRegistry, AssetRecord
from CySIEM.investigation.investigation_fabric import investigate_host, find_related_hosts

app = FastAPI(title="KKSIEM API", version="0.1.0")
_opensearch = OpenSearchClient()
_producer = KafkaProducerClient(settings.kafka_bootstrap_servers, client_id="kksiem-api")
_correlation_store = CorrelationStore()
_assets = AssetRegistry()


@app.get("/health")
def health():
    """Checks the API's own dependencies, not just liveness of the process -
    an enterprise deployment needs /health to mean something for load
    balancers and orchestrators, not just 'the process is running'."""
    redis_ok = _correlation_store.health_check()
    try:
        opensearch_ok = _opensearch.client.ping()
    except Exception:
        opensearch_ok = False

    status = "ok" if (redis_ok and opensearch_ok) else "degraded"
    return {"status": status, "redis": redis_ok, "opensearch": opensearch_ok}


@app.get("/events/{host}")
def get_host_events(host: str, hours: int = Query(24, ge=1, le=168)):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    try:
        events = _opensearch.query_host_history(host, start, end, size=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"host": host, "count": len(events), "events": events}


@app.get("/alerts")
def get_alerts(limit: int = Query(50, ge=1, le=200)):
    # In a fuller build this would query an alerts index; for now this is a
    # placeholder documenting the intended shape - alerts are also fully
    # visible by consuming the alerts.confirmed Kafka topic directly.
    return {"note": "Query the alerts.confirmed Kafka topic, or extend this endpoint to index alerts into OpenSearch."}


@app.post("/verdicts")
def submit_verdict(verdict: HumanVerdict):
    """
    Analyst submits a true/false-positive verdict on an alert. Published to
    human.verdicts - nothing consumes this yet (Layer 11 Learning Fabric
    doesn't exist in v1), but capturing it now means that data already
    exists once that layer is built, rather than starting from zero.
    """
    try:
        _producer.send(settings.topic(settings.topic_human_verdicts), value=verdict, key=verdict.source_host)
        _producer.flush(timeout=5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record verdict: {e}")
    return {"status": "recorded", "verdict_id": verdict.verdict_id}


@app.put("/assets/{host}")
def upsert_asset(host: str, record: AssetRecord, tenant_id: str = Query(settings.tenant_id)):
    """Register or update an asset's business context (Layer 2A). E.g.
    PUT /assets/WIN-SRV01 {"host": "WIN-SRV01", "criticality": "critical",
    "owner": "IT-team", "asset_type": "domain_controller"}
    tenant_id defaults to this install's own tenant."""
    if record.host != host:
        record = record.model_copy(update={"host": host})
    _assets.upsert(record, tenant_id=tenant_id)
    return {"status": "registered", "host": host, "tenant_id": tenant_id}


@app.get("/assets/{host}")
def get_asset(host: str, tenant_id: str = Query(settings.tenant_id)):
    return _assets.get(host, tenant_id=tenant_id)


@app.get("/assets")
def list_assets(tenant_id: str = Query(settings.tenant_id)):
    return {"assets": _assets.list_all(tenant_id=tenant_id)}


@app.delete("/assets/{host}")
def delete_asset(host: str, tenant_id: str = Query(settings.tenant_id)):
    _assets.delete(host, tenant_id=tenant_id)
    return {"status": "deleted", "host": host, "tenant_id": tenant_id}


@app.get("/investigate/{host}")
def investigate(host: str, hours: int = Query(24, ge=1, le=168)):
    """Layer 6 Investigation Fabric: full timeline + asset context + stats
    for a host in one call. Same query Agent 4 runs during verification,
    exposed here for manual analyst investigation."""
    try:
        report = investigate_host(host, lookback_hours=hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return report


@app.get("/investigate/{host}/related")
def related_hosts(host: str, hours: int = Query(24, ge=1, le=168)):
    """Basic Layer 3B substitute: hosts/IPs that co-occurred with this host's
    traffic in the given window. Not a real graph - see roadmap_stubs.py."""
    try:
        related = find_related_hosts(host, lookback_hours=hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"host": host, "related_ips": related}
