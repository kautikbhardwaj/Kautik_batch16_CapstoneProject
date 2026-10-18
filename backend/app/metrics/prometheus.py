from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import CostRecord, ResourceMetric, AlertIncident, CostRecommendation

# Prometheus Gauges and Counters
CLOUD_COST_TOTAL = Gauge(
    "cloud_cost_total_usd",
    "Current month-to-date cloud spend in USD",
    ["provider", "environment"]
)

CLOUD_RESOURCE_CPU = Gauge(
    "cloud_resource_cpu_percent",
    "Real-time CPU utilization percentage",
    ["provider", "resource_name", "environment"]
)

CLOUD_RESOURCE_MEM = Gauge(
    "cloud_resource_memory_percent",
    "Real-time Memory utilization percentage",
    ["provider", "resource_name", "environment"]
)

CLOUD_ACTIVE_ALERTS = Gauge(
    "cloud_active_alerts_total",
    "Count of active unresolved alerts",
    ["severity"]
)

CLOUD_POTENTIAL_SAVINGS = Gauge(
    "cloud_potential_savings_usd",
    "Estimated monthly savings from idle/rightsizing recommendations",
    ["recommendation_type"]
)


def update_prometheus_metrics(db: Session):
    """Update all Prometheus gauges with latest database telemetry"""
    # 1. Update costs
    cost_rows = db.query(
        CostRecord.provider,
        CostRecord.environment,
        func.sum(CostRecord.cost_usd)
    ).group_by(CostRecord.provider, CostRecord.environment).all()

    for p, env, total in cost_rows:
        CLOUD_COST_TOTAL.labels(provider=p, environment=env).set(float(total or 0.0))

    # 2. Update resource metrics
    resources = db.query(ResourceMetric).all()
    for r in resources:
        CLOUD_RESOURCE_CPU.labels(
            provider=r.provider,
            resource_name=r.resource_name,
            environment=r.environment
        ).set(r.cpu_utilization_pct)
        
        CLOUD_RESOURCE_MEM.labels(
            provider=r.provider,
            resource_name=r.resource_name,
            environment=r.environment
        ).set(r.memory_utilization_pct)

    # 3. Update active alerts
    for sev in ["critical", "warning", "info"]:
        count = db.query(AlertIncident).filter(
            AlertIncident.severity == sev,
            AlertIncident.status == "active"
        ).count()
        CLOUD_ACTIVE_ALERTS.labels(severity=sev).set(count)

    # 4. Update potential savings
    rec_rows = db.query(
        CostRecommendation.recommendation_type,
        func.sum(CostRecommendation.estimated_monthly_savings)
    ).filter(CostRecommendation.status == "pending").group_by(CostRecommendation.recommendation_type).all()

    for r_type, savings in rec_rows:
        CLOUD_POTENTIAL_SAVINGS.labels(recommendation_type=r_type).set(float(savings or 0.0))


def get_prometheus_metrics(db: Session) -> bytes:
    update_prometheus_metrics(db)
    return generate_latest()
