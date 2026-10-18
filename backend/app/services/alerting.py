import logging
from datetime import datetime, date, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import AlertRule, AlertIncident, ResourceMetric, CostRecord
from backend.app.services.notifier import NotificationDispatcher

logger = logging.getLogger(__name__)

DEFAULT_RULES = [
    {
        "name": "High CPU Utilization Critical",
        "description": "Fired when any cloud compute instance exceeds 85% CPU utilization",
        "metric_type": "high_cpu",
        "provider": "ALL",
        "environment": "ALL",
        "threshold_value": 85.0,
        "operator": "gt",
        "severity": "critical",
        "notification_channel": "slack",
        "enabled": True
    },
    {
        "name": "High Memory Utilization Warning",
        "description": "Fired when any cloud resource exceeds 80% RAM utilization",
        "metric_type": "high_memory",
        "provider": "ALL",
        "environment": "ALL",
        "threshold_value": 80.0,
        "operator": "gt",
        "severity": "warning",
        "notification_channel": "slack",
        "enabled": True
    },
    {
        "name": "Daily Cost Spike Alert",
        "description": "Triggered when daily spend exceeds $150 in any single service",
        "metric_type": "cost_daily_spike",
        "provider": "ALL",
        "environment": "production",
        "threshold_value": 150.0,
        "operator": "gt",
        "severity": "warning",
        "notification_channel": "slack",
        "enabled": True
    },
    {
        "name": "Idle Compute Resource Alert",
        "description": "Detects instances with < 5% CPU utilization running continuously",
        "metric_type": "idle_resource",
        "provider": "ALL",
        "environment": "development",
        "threshold_value": 5.0,
        "operator": "lt",
        "severity": "info",
        "notification_channel": "slack",
        "enabled": True
    }
]


class AlertEngine:
    @staticmethod
    def initialize_default_rules(db: Session):
        """Seed default DevOps alert rules if table is empty"""
        count = db.query(AlertRule).count()
        if count == 0:
            logger.info("Initializing default DevOps alert rules...")
            for r in DEFAULT_RULES:
                rule = AlertRule(**r)
                db.add(rule)
            db.commit()

    @staticmethod
    async def evaluate_rules(db: Session) -> List[AlertIncident]:
        """
        Evaluate active alert rules against live resource metrics and cost records.
        """
        rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()
        new_incidents: List[AlertIncident] = []

        for rule in rules:
            if rule.metric_type == "high_cpu":
                query = db.query(ResourceMetric).filter(ResourceMetric.cpu_utilization_pct > rule.threshold_value)
                if rule.provider != "ALL":
                    query = query.filter(ResourceMetric.provider == rule.provider)
                if rule.environment != "ALL":
                    query = query.filter(ResourceMetric.environment == rule.environment)

                for res in query.all():
                    # Check for active unresolved incident
                    existing = db.query(AlertIncident).filter(
                        AlertIncident.rule_id == rule.id,
                        AlertIncident.resource_id == res.resource_id,
                        AlertIncident.status == "active"
                    ).first()

                    if not existing:
                        incident = AlertIncident(
                            rule_id=rule.id,
                            title=f"High CPU on {res.resource_name} ({res.provider})",
                            message=f"CPU utilization reached {res.cpu_utilization_pct:.1f}% (threshold: > {rule.threshold_value:.1f}%) in {res.environment}.",
                            provider=res.provider,
                            service=res.service,
                            resource_id=res.resource_id,
                            metric_type="high_cpu",
                            current_value=res.cpu_utilization_pct,
                            threshold_value=rule.threshold_value,
                            severity=rule.severity,
                            status="active",
                            triggered_at=datetime.utcnow()
                        )
                        db.add(incident)
                        new_incidents.append(incident)
                        await NotificationDispatcher.send_slack_alert(
                            webhook_url=rule.webhook_url,
                            title=incident.title,
                            message=incident.message,
                            severity=incident.severity,
                            metadata={"Provider": res.provider, "Resource": res.resource_name, "CPU": f"{res.cpu_utilization_pct}%"}
                        )

            elif rule.metric_type == "cost_daily_spike":
                # Check recent high daily costs
                recent_day = date.today() - timedelta(days=3)
                query = db.query(CostRecord).filter(
                    CostRecord.record_date >= recent_day,
                    CostRecord.cost_usd > rule.threshold_value
                )
                if rule.provider != "ALL":
                    query = query.filter(CostRecord.provider == rule.provider)
                if rule.environment != "ALL":
                    query = query.filter(CostRecord.environment == rule.environment)

                for cost in query.all():
                    existing = db.query(AlertIncident).filter(
                        AlertIncident.rule_id == rule.id,
                        AlertIncident.service == cost.service,
                        AlertIncident.status == "active"
                    ).first()

                    if not existing:
                        incident = AlertIncident(
                            rule_id=rule.id,
                            title=f"Cost Spike on {cost.provider} {cost.service}",
                            message=f"Daily spend spiked to ${cost.cost_usd:.2f} (threshold: > ${rule.threshold_value:.2f}) on {cost.record_date}.",
                            provider=cost.provider,
                            service=cost.service,
                            resource_id=cost.resource_id,
                            metric_type="cost_daily_spike",
                            current_value=cost.cost_usd,
                            threshold_value=rule.threshold_value,
                            severity=rule.severity,
                            status="active",
                            triggered_at=datetime.utcnow()
                        )
                        db.add(incident)
                        new_incidents.append(incident)
                        await NotificationDispatcher.send_slack_alert(
                            webhook_url=rule.webhook_url,
                            title=incident.title,
                            message=incident.message,
                            severity=incident.severity,
                            metadata={"Provider": cost.provider, "Service": cost.service, "Daily Cost": f"${cost.cost_usd:.2f}"}
                        )

        db.commit()
        return new_incidents
