from typing import List, Dict, Any


def collect_evidence(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a lightweight evidence list from alerts."""
    return [
        {
            "id": alert.get("id"),
            "title": alert.get("title"),
            "source": alert.get("source"),
            "target": alert.get("target"),
        }
        for alert in alerts
    ]
