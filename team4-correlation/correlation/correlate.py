from collections import defaultdict
from typing import List, Dict, Any


def correlate_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group alerts into incidents based on shared target and time proximity."""
    incidents = []
    grouped = defaultdict(list)

    for alert in alerts:
        grouped[alert.get("target", "unknown")].append(alert)

    for target, target_alerts in grouped.items():
        target_alerts = sorted(target_alerts, key=lambda item: item.get("timestamp", ""))
        incidents.append({
            "target": target,
            "alerts": target_alerts,
            "summary": f"Potential incident on {target}",
        })

    return incidents
