import logging
import json
from typing import Optional, Dict, Any
import httpx
from backend.app.config import settings

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """
    Dispatches alerts to Slack, Microsoft Teams, or custom Webhooks.
    """

    @staticmethod
    async def send_slack_alert(
        webhook_url: Optional[str],
        title: str,
        message: str,
        severity: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        target_url = webhook_url or settings.SLACK_WEBHOOK_URL
        if not target_url:
            logger.info(f"[SIMULATED SLACK ALERT] Severity: {severity.upper()} | {title} - {message}")
            return True

        color_map = {
            "critical": "#FF0000",
            "warning": "#FFA500",
            "info": "#36A64F"
        }
        color = color_map.get(severity.lower(), "#808080")

        fields = []
        if metadata:
            for k, v in metadata.items():
                fields.append({"title": k.replace("_", " ").title(), "value": str(v), "short": True})

        payload = {
            "text": f"🚨 *{title}* ({severity.upper()})",
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": fields,
                    "footer": "DevOps Multi-Cloud Cost & Resource Monitor",
                    "ts": int(logging.time.time())
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(target_url, json=payload)
                if res.status_code == 200:
                    logger.info("Successfully sent Slack alert notification.")
                    return True
                else:
                    logger.warning(f"Slack webhook returned status code {res.status_code}: {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Error dispatching Slack webhook: {e}")
            return False

    @staticmethod
    async def send_teams_alert(
        webhook_url: Optional[str],
        title: str,
        message: str,
        severity: str
    ) -> bool:
        target_url = webhook_url or settings.TEAMS_WEBHOOK_URL
        if not target_url:
            logger.info(f"[SIMULATED TEAMS ALERT] Severity: {severity.upper()} | {title} - {message}")
            return True

        theme_color = "d9534f" if severity == "critical" else ("f0ad4e" if severity == "warning" else "5cb85c")
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": title,
            "sections": [{
                "activityTitle": f"DevOps Alert: {title}",
                "activitySubtitle": f"Severity: {severity.upper()}",
                "text": message
            }]
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(target_url, json=payload)
                return res.status_code == 200
        except Exception as e:
            logger.error(f"Error dispatching Teams webhook: {e}")
            return False
