import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models import CostRecord, ResourceMetric, ProviderStatus
from backend.app.services.cloud import get_cloud_connectors

logger = logging.getLogger(__name__)


class CloudDataAggregator:
    """
    Central Data Ingestion & Normalization Engine.
    Aggregates disparate cost and resource metrics from AWS, Azure, and GCP,
    transforms them into the unified relational schema, and updates database records.
    """

    @staticmethod
    def sync_all_clouds(db: Session, days_back: int = 30) -> Dict[str, Any]:
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        connectors = get_cloud_connectors()
        results = {}

        total_cost_records = 0
        total_metrics_records = 0

        for provider, connector in connectors.items():
            logger.info(f"Synchronizing data for cloud provider: {provider}...")
            
            # 1. Test status
            conn_test = connector.test_connection()
            status_entry = db.query(ProviderStatus).filter(ProviderStatus.provider == provider).first()
            if not status_entry:
                status_entry = ProviderStatus(provider=provider)
                db.add(status_entry)

            status_entry.status = "connected" if conn_test.get("connected") else "error"
            status_entry.message = conn_test.get("message", "OK")
            status_entry.last_sync_at = datetime.utcnow()

            # 2. Fetch and store cost records
            try:
                costs = connector.fetch_costs(start_date=start_date, end_date=end_date)
                # Remove existing records for this provider in the date range to avoid duplicates during re-sync
                db.query(CostRecord).filter(
                    CostRecord.provider == provider,
                    CostRecord.record_date >= start_date,
                    CostRecord.record_date <= end_date
                ).delete()

                for c in costs:
                    rec = CostRecord(
                        provider=c.provider,
                        service=c.service,
                        resource_id=c.resource_id,
                        environment=c.environment,
                        region=c.region,
                        cost_usd=c.cost_usd,
                        usage_amount=c.usage_amount,
                        usage_unit=c.usage_unit,
                        record_date=c.record_date,
                        tags=c.tags
                    )
                    db.add(rec)
                
                total_cost_records += len(costs)
                status_entry.records_synced = len(costs)
            except Exception as e:
                logger.error(f"Failed to ingest costs for {provider}: {e}")
                status_entry.message = f"Cost sync error: {str(e)}"

            # 3. Fetch and store resource metrics (telemetry)
            try:
                resources = connector.fetch_resource_metrics()
                # Clear previous metrics for this provider to keep real-time view current
                db.query(ResourceMetric).filter(ResourceMetric.provider == provider).delete()

                for r in resources:
                    metric = ResourceMetric(
                        provider=r.provider,
                        service=r.service,
                        resource_id=r.resource_id,
                        resource_name=r.resource_name,
                        environment=r.environment,
                        region=r.region,
                        cpu_utilization_pct=r.cpu_utilization_pct,
                        memory_utilization_pct=r.memory_utilization_pct,
                        disk_utilization_gb=r.disk_utilization_gb,
                        network_in_mb=r.network_in_mb,
                        network_out_mb=r.network_out_mb,
                        status=r.status,
                        timestamp=r.timestamp
                    )
                    db.add(metric)

                total_metrics_records += len(resources)
            except Exception as e:
                logger.error(f"Failed to ingest metrics for {provider}: {e}")

            db.commit()
            results[provider] = {
                "status": status_entry.status,
                "costs_synced": len(costs) if 'costs' in locals() else 0,
                "resources_synced": len(resources) if 'resources' in locals() else 0
            }

        logger.info(f"Cloud synchronization complete: {total_cost_records} cost rows, {total_metrics_records} metric rows.")
        return {
            "summary": {
                "total_cost_records": total_cost_records,
                "total_metrics_records": total_metrics_records,
                "sync_timestamp": datetime.utcnow().isoformat()
            },
            "providers": results
        }
