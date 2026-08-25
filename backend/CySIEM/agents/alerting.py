"""
Alert delivery. Called by Agent 3 once Agent 4 confirms. Currently supports
a Slack incoming webhook; extend with email/PagerDuty/etc as needed - this
is intentionally a single function so adding a channel means adding one
branch here, not touching agent3.
"""
from __future__ import annotations
import logging
import httpx
from CySIEM.common.config import settings
from CySIEM.schemas.agent_io import FinalAlert

logger = logging.getLogger("kksiem.agents.alerting")


def _format_slack_message(alert: FinalAlert) -> dict:
    return {
        "text": (
            f":rotating_light: *{alert.severity.upper()} - {alert.title}*\n"
            f"*Host:* {alert.source_host} (`{alert.source_segment}`)\n"
            f"*Summary:* {alert.summary}\n\n"
            f"*Agent 1 (tool-based):* {alert.agent1_summary}\n"
            f"*Agent 2 (log-based):* {alert.agent2_summary}\n"
            f"*Verification:* {alert.verification_summary}\n"
            f"*MITRE:* {', '.join(alert.mitre_techniques) or 'n/a'}\n"
            f"*Alert ID:* `{alert.alert_id}`"
        )
    }


def push_alert(alert: FinalAlert):
    logger.warning(f"ALERT: [{alert.severity}] {alert.title} host={alert.source_host}")

    if not settings.slack_webhook_url:
        logger.info("SLACK_WEBHOOK_URL not configured - alert logged only")
        return

    try:
        resp = httpx.post(settings.slack_webhook_url, json=_format_slack_message(alert), timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to deliver alert to Slack: {e}")
