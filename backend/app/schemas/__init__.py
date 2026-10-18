from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Cost Schemas
class CostRecordBase(BaseModel):
    provider: str
    service: str
    resource_id: Optional[str] = None
    environment: str = "production"
    region: Optional[str] = None
    cost_usd: float
    usage_amount: float = 0.0
    usage_unit: Optional[str] = None
    record_date: date
    tags: Optional[Dict[str, str]] = None


class CostRecordCreate(CostRecordBase):
    pass


class CostRecordResponse(CostRecordBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Resource Metric Schemas
class ResourceMetricBase(BaseModel):
    provider: str
    service: str
    resource_id: str
    resource_name: str
    environment: str = "production"
    region: Optional[str] = None
    cpu_utilization_pct: float
    memory_utilization_pct: float
    disk_utilization_gb: float
    network_in_mb: float = 0.0
    network_out_mb: float = 0.0
    status: str = "running"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ResourceMetricResponse(ResourceMetricBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Alert Rule Schemas
class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    metric_type: str  # cost_daily_spike, cost_monthly_budget, high_cpu, high_memory, idle_resource
    provider: str = "ALL"
    environment: str = "ALL"
    threshold_value: float
    operator: str = "gt"
    severity: str = "warning"
    notification_channel: str = "slack"
    webhook_url: Optional[str] = None
    enabled: bool = True


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleResponse(AlertRuleBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Alert Incident Schemas
class AlertIncidentResponse(BaseModel):
    id: int
    rule_id: Optional[int]
    title: str
    message: str
    provider: str
    service: Optional[str]
    resource_id: Optional[str]
    metric_type: str
    current_value: float
    threshold_value: float
    severity: str
    status: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


# Recommendation Schemas
class CostRecommendationResponse(BaseModel):
    id: int
    provider: str
    service: str
    resource_id: str
    resource_name: str
    recommendation_type: str
    title: str
    description: str
    current_monthly_cost: float
    estimated_monthly_savings: float
    status: str
    action_plan: Optional[str]
    detected_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Dashboard Summary & Aggregation Schemas
class ProviderSpend(BaseModel):
    provider: str
    total_cost: float
    percentage: float
    services_count: int


class ServiceSpend(BaseModel):
    service: str
    provider: str
    total_cost: float


class DailyCostPoint(BaseModel):
    date: str
    AWS: float = 0.0
    Azure: float = 0.0
    GCP: float = 0.0
    total: float = 0.0


class DashboardOverview(BaseModel):
    total_spend_month_to_date: float
    projected_spend_month_end: float
    month_over_month_change_pct: float
    total_potential_savings: float
    active_alerts_count: int
    total_resources_monitored: int
    provider_breakdown: List[ProviderSpend]
    top_cost_services: List[ServiceSpend]
    daily_spend_trend: List[DailyCostPoint]
    idle_resources_count: int
    high_utilization_count: int


class ProviderSyncStatusResponse(BaseModel):
    provider: str
    status: str
    last_sync_at: Optional[datetime]
    message: Optional[str]
    records_synced: int
    model_config = ConfigDict(from_attributes=True)
