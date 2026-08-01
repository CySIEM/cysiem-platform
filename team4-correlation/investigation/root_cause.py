from typing import List, Dict, Any


def suggest_root_cause(alerts: List[Dict[str, Any]]) -> str:
    """Provide a simple root cause suggestion based on alert titles."""
    titles = [str(alert.get("title", "")).lower() for alert in alerts]
    if any("failed login" in title for title in titles):
        return "Possible brute-force or credential abuse activity"
    if any("suspicious process" in title for title in titles):
        return "Potential malicious process execution"
    return "Investigation required"
