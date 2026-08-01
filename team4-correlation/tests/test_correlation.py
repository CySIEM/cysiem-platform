import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from correlation.correlate import correlate_alerts
from correlation.deduplicate import deduplicate_alerts
from correlation.severity import calculate_severity


def test_deduplicate_alerts_removes_duplicates():
    alerts = [
        {"id": "a1", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
        {"id": "a1", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
        {"id": "a2", "source": "linux", "target": "server-02", "timestamp": "2026-08-01T10:05:00Z", "title": "Suspicious process"},
    ]

    result = deduplicate_alerts(alerts)

    assert len(result) == 2
    assert result[0]["id"] == "a1"


def test_correlate_alerts_groups_related_events():
    alerts = [
        {"id": "a1", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
        {"id": "a2", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:03:00Z", "title": "Failed login"},
        {"id": "a3", "source": "linux", "target": "server-02", "timestamp": "2026-08-01T10:10:00Z", "title": "Suspicious process"},
    ]

    incidents = correlate_alerts(alerts)

    assert len(incidents) == 2
    assert incidents[0]["alerts"][0]["id"] == "a1"


def test_calculate_severity_returns_score():
    alerts = [
        {"severity": "high"},
        {"severity": "medium"},
        {"severity": "low"},
    ]

    score = calculate_severity(alerts)

    assert score >= 50
