import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models import ResourceMetric, CostRecommendation, CostRecord

logger = logging.getLogger(__name__)


class CostOptimizationEngine:
    """
    Analyzes resource telemetry and spending patterns to detect cloud waste,
    unattached disks, oversized instances, and generates quantified savings recommendations.
    """

    @staticmethod
    def evaluate_optimizations(db: Session) -> List[CostRecommendation]:
        logger.info("Running Cloud Cost Optimization analysis...")
        recommendations: List[CostRecommendation] = []

        # 1. Detect Idle Instances (CPU < 5% in dev/staging or status='idle')
        idle_resources = db.query(ResourceMetric).filter(
            (ResourceMetric.cpu_utilization_pct < 5.0) | (ResourceMetric.status == "idle")
        ).all()

        for res in idle_resources:
            # Check if recommendation already recorded
            existing = db.query(CostRecommendation).filter(
                CostRecommendation.resource_id == res.resource_id,
                CostRecommendation.recommendation_type == "idle_resource",
                CostRecommendation.status == "pending"
            ).first()

            if not existing:
                monthly_cost = round(res.disk_utilization_gb * 0.12 + 65.0, 2)
                rec = CostRecommendation(
                    provider=res.provider,
                    service=res.service,
                    resource_id=res.resource_id,
                    resource_name=res.resource_name,
                    recommendation_type="idle_resource",
                    title=f"Terminate or Schedule Idle {res.service} ({res.resource_name})",
                    description=(
                        f"Resource '{res.resource_name}' in {res.environment} has average CPU utilization "
                        f"of only {res.cpu_utilization_pct:.1f}% over the observation period."
                    ),
                    current_monthly_cost=monthly_cost,
                    estimated_monthly_savings=round(monthly_cost * 0.90, 2),
                    status="pending",
                    action_plan=(
                        f"1. Validate workload dependencies in {res.environment} environment.\n"
                        f"2. Stop instance or configure automated shutdown schedule outside working hours.\n"
                        f"3. Create AMI/snapshot backup and terminate if obsolete."
                    ),
                    detected_at=datetime.utcnow()
                )
                db.add(rec)
                recommendations.append(rec)

        # 2. Detect Rightsizing Opportunities (CPU between 5% and 20%)
        oversized = db.query(ResourceMetric).filter(
            ResourceMetric.cpu_utilization_pct >= 5.0,
            ResourceMetric.cpu_utilization_pct <= 20.0,
            ResourceMetric.status == "running"
        ).all()

        for res in oversized:
            existing = db.query(CostRecommendation).filter(
                CostRecommendation.resource_id == res.resource_id,
                CostRecommendation.recommendation_type == "rightsizing",
                CostRecommendation.status == "pending"
            ).first()

            if not existing:
                cur_cost = 180.0
                savings = 110.0
                rec = CostRecommendation(
                    provider=res.provider,
                    service=res.service,
                    resource_id=res.resource_id,
                    resource_name=res.resource_name,
                    recommendation_type="rightsizing",
                    title=f"Downsize Oversized Instance: {res.resource_name}",
                    description=(
                        f"Average CPU utilization is {res.cpu_utilization_pct:.1f}% and memory is {res.memory_utilization_pct:.1f}%. "
                        f"Instance is over-provisioned for its actual workload."
                    ),
                    current_monthly_cost=cur_cost,
                    estimated_monthly_savings=savings,
                    status="pending",
                    action_plan=(
                        f"1. Downsize instance to next smaller tier (e.g. from 4xlarge to 2xlarge or xlarge).\n"
                        f"2. Verify memory headroom remains above 20% safe margin.\n"
                        f"3. Apply during maintenance window with automated roll-back plan."
                    ),
                    detected_at=datetime.utcnow()
                )
                db.add(rec)
                recommendations.append(rec)

        # 3. Detect Unattached / Orphaned Storage Disks (status == idle and disk > 100GB)
        orphaned_disks = db.query(ResourceMetric).filter(
            ResourceMetric.disk_utilization_gb > 100.0,
            ResourceMetric.cpu_utilization_pct == 0.0
        ).all()

        for d in orphaned_disks:
            existing = db.query(CostRecommendation).filter(
                CostRecommendation.resource_id == d.resource_id,
                CostRecommendation.recommendation_type == "unattached_storage",
                CostRecommendation.status == "pending"
            ).first()

            if not existing:
                disk_cost = round(d.disk_utilization_gb * 0.10, 2)
                rec = CostRecommendation(
                    provider=d.provider,
                    service=d.service,
                    resource_id=d.resource_id,
                    resource_name=d.resource_name,
                    recommendation_type="unattached_storage",
                    title=f"Delete Unattached Storage Volume: {d.resource_name}",
                    description=(
                        f"Unattached volume of {d.disk_utilization_gb:.0f} GB is accruing storage costs "
                        f"without any attached compute instance."
                    ),
                    current_monthly_cost=disk_cost,
                    estimated_monthly_savings=disk_cost,
                    status="pending",
                    action_plan=(
                        f"1. Take snapshot of volume for compliance and disaster recovery.\n"
                        f"2. Delete unattached volume {d.resource_id} via Cloud Console or Terraform."
                    ),
                    detected_at=datetime.utcnow()
                )
                db.add(rec)
                recommendations.append(rec)

        db.commit()
        return recommendations

    @staticmethod
    def get_total_potential_savings(db: Session) -> float:
        total = db.query(CostRecommendation)\
                  .filter(CostRecommendation.status == "pending")\
                  .with_entities(CostRecommendation.estimated_monthly_savings)\
                  .all()
        return round(sum(t[0] for t in total if t[0]), 2)
