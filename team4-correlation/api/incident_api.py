from typing import List, Dict, Any

from correlation.correlate import correlate_alerts
from correlation.deduplicate import deduplicate_alerts
from investigation.timeline import build_timeline


def analyze_incidents(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a simple incident analysis payload."""
    unique_alerts = deduplicate_alerts(alerts)
    incidents = correlate_alerts(unique_alerts)
    timeline = build_timeline(unique_alerts)

    return {
        "alert_count": len(unique_alerts),
        "incident_count": len(incidents),
        "incidents": incidents,
        "timeline": timeline,
    }
