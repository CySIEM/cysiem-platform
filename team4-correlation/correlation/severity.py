from typing import List, Dict, Any


def calculate_severity(alerts: List[Dict[str, Any]]) -> int:
    """Calculate a simple severity score from alert severities."""
    weights = {"low": 20, "medium": 40, "high": 70, "critical": 100}
    score = 0

    for alert in alerts:
        severity = str(alert.get("severity", "low")).lower()
        score += weights.get(severity, 20)

    return min(score, 100)
