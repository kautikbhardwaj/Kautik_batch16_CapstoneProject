from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta
from backend.app.database import get_db
from backend.app.models import AlertIncident, ResourceMetric
from backend.app.schemas import DashboardOverview
from backend.app.services.analytics import CloudAnalyticsEngine
from backend.app.services.optimizer import CostOptimizationEngine

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    provider: Optional[str] = Query(None, description="Filter by cloud provider: ALL, AWS, Azure, GCP"),
    environment: Optional[str] = Query(None, description="Filter by environment: ALL, production, staging, development"),
    days: int = Query(30, ge=1, le=90, description="Number of historical days to inspect"),
    db: Session = Depends(get_db)
):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    run_rate = CloudAnalyticsEngine.calculate_run_rate_and_mom(db)
    provider_breakdown = CloudAnalyticsEngine.get_provider_breakdown(
        db, start_date=start_date, end_date=end_date, environment=environment
    )
    top_services = CloudAnalyticsEngine.get_top_services(
        db, limit=6, start_date=start_date, end_date=end_date, provider=provider, environment=environment
    )
    daily_trend = CloudAnalyticsEngine.get_daily_trend(
        db, start_date=start_date, end_date=end_date, provider=provider, environment=environment
    )
    potential_savings = CostOptimizationEngine.get_total_potential_savings(db)

    active_alerts = db.query(AlertIncident).filter(AlertIncident.status == "active").count()
    total_resources = db.query(ResourceMetric).count()
    idle_count = db.query(ResourceMetric).filter(
        (ResourceMetric.cpu_utilization_pct < 5.0) | (ResourceMetric.status == "idle")
    ).count()
    high_util_count = db.query(ResourceMetric).filter(ResourceMetric.cpu_utilization_pct > 80.0).count()

    return DashboardOverview(
        total_spend_month_to_date=run_rate["month_to_date"],
        projected_spend_month_end=run_rate["projected_month_end"],
        month_over_month_change_pct=run_rate["mom_change_pct"],
        total_potential_savings=potential_savings,
        active_alerts_count=active_alerts,
        total_resources_monitored=total_resources,
        provider_breakdown=provider_breakdown,
        top_cost_services=top_services,
        daily_spend_trend=daily_trend,
        idle_resources_count=idle_count,
        high_utilization_count=high_util_count
    )
