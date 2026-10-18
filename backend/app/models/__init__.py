from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class CostRecord(Base):
    __tablename__ = "cost_records"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), index=True, nullable=False)  # AWS, Azure, GCP
    service = Column(String(100), index=True, nullable=False)   # EC2, S3, BigQuery, VM, etc.
    resource_id = Column(String(200), index=True, nullable=True)
    environment = Column(String(30), index=True, nullable=False, default="production") # production, staging, development
    region = Column(String(50), nullable=True)
    cost_usd = Column(Float, nullable=False, default=0.0)
    usage_amount = Column(Float, nullable=False, default=0.0)
    usage_unit = Column(String(30), nullable=True)             # Hours, GB, Requests
    record_date = Column(Date, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON, nullable=True)


class ResourceMetric(Base):
    __tablename__ = "resource_metrics"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), index=True, nullable=False)
    service = Column(String(100), index=True, nullable=False)
    resource_id = Column(String(200), index=True, nullable=False)
    resource_name = Column(String(200), nullable=False)
    environment = Column(String(30), index=True, nullable=False, default="production")
    region = Column(String(50), nullable=True)
    cpu_utilization_pct = Column(Float, nullable=False, default=0.0)
    memory_utilization_pct = Column(Float, nullable=False, default=0.0)
    disk_utilization_gb = Column(Float, nullable=False, default=0.0)
    network_in_mb = Column(Float, nullable=False, default=0.0)
    network_out_mb = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default="running") # running, idle, stopped
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    metric_type = Column(String(50), nullable=False) # cost_daily_spike, cost_monthly_budget, high_cpu, high_memory, idle_resource
    provider = Column(String(20), nullable=False, default="ALL") # ALL, AWS, Azure, GCP
    environment = Column(String(30), nullable=False, default="ALL") # ALL, production, staging, development
    threshold_value = Column(Float, nullable=False)
    operator = Column(String(10), nullable=False, default="gt") # gt, lt, gte, lte, eq
    severity = Column(String(20), nullable=False, default="warning") # critical, warning, info
    notification_channel = Column(String(50), nullable=False, default="slack") # slack, teams, webhook, email
    webhook_url = Column(String(500), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    incidents = relationship("AlertIncident", back_populates="rule", cascade="all, delete-orphan")


class AlertIncident(Base):
    __tablename__ = "alert_incidents"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    provider = Column(String(20), nullable=False)
    service = Column(String(100), nullable=True)
    resource_id = Column(String(200), nullable=True)
    metric_type = Column(String(50), nullable=False)
    current_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False, default="warning") # critical, warning, info
    status = Column(String(30), nullable=False, default="active")   # active, acknowledged, resolved
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    rule = relationship("AlertRule", back_populates="incidents")


class CostRecommendation(Base):
    __tablename__ = "cost_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), index=True, nullable=False)
    service = Column(String(100), nullable=False)
    resource_id = Column(String(200), index=True, nullable=False)
    resource_name = Column(String(200), nullable=False)
    recommendation_type = Column(String(50), nullable=False) # idle_resource, rightsizing, unattached_storage, reserved_savings
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    current_monthly_cost = Column(Float, nullable=False, default=0.0)
    estimated_monthly_savings = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default="pending") # pending, applied, dismissed
    action_plan = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)


class ProviderStatus(Base):
    __tablename__ = "provider_statuses"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), unique=True, nullable=False) # AWS, Azure, GCP
    status = Column(String(30), nullable=False, default="connected") # connected, mock_mode, error, syncing
    last_sync_at = Column(DateTime, nullable=True)
    message = Column(String(255), nullable=True)
    records_synced = Column(Integer, default=0)
