from datetime import datetime
from typing import List, Dict, Any


def build_timeline(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return alerts sorted chronologically by timestamp."""
    return sorted(alerts, key=lambda item: item.get("timestamp", ""))
