from typing import List, Dict, Any


def deduplicate_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate alerts by id while preserving order."""
    seen = set()
    unique_alerts = []

    for alert in alerts:
        alert_id = alert.get("id")
        if alert_id in seen:
            continue
        seen.add(alert_id)
        unique_alerts.append(alert)

    return unique_alerts
