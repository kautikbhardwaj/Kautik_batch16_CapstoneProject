from datetime import date, datetime, timedelta, timezone
import random
from typing import List
from backend.app.schemas import CostRecordBase, ResourceMetricBase

# Seed for reproducible realistic baseline, with realistic variances
random.seed(42)

SERVICES = {
    "AWS": [
        ("Amazon Elastic Compute Cloud - Compute", "EC2", 45.0, 150.0, "Hrs"),
        ("Amazon Simple Storage Service", "S3", 15.0, 40.0, "GB-Mo"),
        ("Amazon Relational Database Service", "RDS", 30.0, 95.0, "Hrs"),
        ("AWS Lambda", "Lambda", 2.0, 15.0, "Requests"),
        ("Amazon DynamoDB", "DynamoDB", 10.0, 35.0, "CapacityUnits"),
        ("Amazon CloudFront", "CloudFront", 5.0, 20.0, "GB-Out"),
    ],
    "Azure": [
        ("Virtual Machines", "Azure VM", 40.0, 130.0, "Hrs"),
        ("Storage Accounts", "Blob Storage", 12.0, 35.0, "GB-Mo"),
        ("Azure SQL Database", "Azure SQL", 28.0, 85.0, "Hrs"),
        ("Azure App Service", "App Service", 18.0, 50.0, "Hrs"),
        ("Azure Cosmos DB", "Cosmos DB", 14.0, 45.0, "RU/s"),
    ],
    "GCP": [
        ("Compute Engine", "Compute Engine", 38.0, 120.0, "Hrs"),
        ("Cloud Storage", "Cloud Storage", 10.0, 30.0, "GB-Mo"),
        ("Cloud SQL", "Cloud SQL", 25.0, 75.0, "Hrs"),
        ("BigQuery", "BigQuery", 20.0, 90.0, "TB-Processed"),
        ("Google Kubernetes Engine", "GKE", 35.0, 110.0, "Cluster-Hrs"),
    ]
}

ENVIRONMENTS = ["production", "staging", "development"]
ENV_WEIGHTS = [0.65, 0.25, 0.10]


def generate_mock_costs(provider: str, start_date: date, end_date: date) -> List[CostRecordBase]:
    records: List[CostRecordBase] = []
    delta = (end_date - start_date).days + 1
    services = SERVICES.get(provider, [])

    for i in range(delta):
        current_date = start_date + timedelta(days=i)
        days_from_end = (end_date - current_date).days

        for full_name, short_name, min_cost, max_cost, unit in services:
            for env in ENVIRONMENTS:
                env_multiplier = 1.0 if env == "production" else (0.35 if env == "staging" else 0.15)
                
                # Base random cost with gentle day-to-day trend
                base_cost = random.uniform(min_cost, max_cost) * env_multiplier
                
                # Inject a realistic DevOps Cost Anomaly (3 days ago on AWS RDS or BigQuery)
                is_anomaly = False
                if days_from_end == 3 and short_name in ["RDS", "BigQuery"] and env == "production":
                    base_cost *= 2.8  # 180% cost spike due to unoptimized query/job
                    is_anomaly = True

                usage = base_cost * random.uniform(1.2, 2.5)

                records.append(
                    CostRecordBase(
                        provider=provider,
                        service=short_name,
                        resource_id=f"{provider.lower()}-{short_name.lower().replace(' ', '-')}-{env}-01",
                        environment=env,
                        region="us-east-1" if provider == "AWS" else ("eastus" if provider == "Azure" else "us-central1"),
                        cost_usd=round(base_cost, 2),
                        usage_amount=round(usage, 2),
                        usage_unit=unit,
                        record_date=current_date,
                        tags={
                            "environment": env,
                            "managed_by": "terraform",
                            "team": "core-devops" if env == "production" else "engineering",
                            "anomaly": "true" if is_anomaly else "false"
                        }
                    )
                )

    return records


def generate_mock_resources(provider: str) -> List[ResourceMetricBase]:
    resources: List[ResourceMetricBase] = []
    now = datetime.now(timezone.utc)

    configs = {
        "AWS": [
            ("i-0a1b2c3d4e5f0001", "api-gateway-prod", "EC2", "production", "us-east-1", 72.5, 68.0, 120.0, "running"),
            ("i-0a1b2c3d4e5f0002", "payment-service-prod", "EC2", "production", "us-east-1", 89.4, 84.2, 250.0, "running"), # High CPU alert trigger!
            ("i-0a1b2c3d4e5f0003", "qa-testing-worker-dev", "EC2", "development", "us-east-1", 3.2, 12.0, 50.0, "idle"),     # Idle Resource candidate
            ("i-0a1b2c3d4e5f0004", "batch-processor-staging", "EC2", "staging", "us-west-2", 14.0, 35.0, 100.0, "running"),   # Rightsizing candidate (m5.4xlarge)
            ("vol-09988776655443", "unattached-data-volume", "EBS", "production", "us-east-1", 0.0, 0.0, 500.0, "idle"),      # Orphaned disk
            ("rds-prod-postgres", "production-db-primary", "RDS", "production", "us-east-1", 64.0, 78.0, 450.0, "running"),
        ],
        "Azure": [
            ("vm-azure-frontend-01", "web-portal-prod", "Azure VM", "production", "eastus", 61.0, 59.0, 80.0, "running"),
            ("vm-azure-worker-dev", "analytics-sandbox-dev", "Azure VM", "development", "eastus", 2.8, 14.0, 60.0, "idle"),    # Idle Resource candidate
            ("vm-azure-ml-training", "recommendation-ml-prod", "Azure VM", "production", "centralus", 91.2, 88.5, 320.0, "running"), # High CPU/RAM
            ("sqldb-azure-crm", "customer-crm-db", "Azure SQL", "production", "eastus", 45.0, 52.0, 200.0, "running"),
            ("disk-azure-orphaned-99", "legacy-backup-disk", "Blob Storage", "staging", "eastus", 0.0, 0.0, 350.0, "idle"),
        ],
        "GCP": [
            ("gcp-gke-node-pool-1", "k8s-cluster-prod-pool", "GKE", "production", "us-central1", 76.0, 71.0, 200.0, "running"),
            ("gcp-instance-dev-test", "legacy-migration-vm", "Compute Engine", "development", "us-central1", 4.1, 10.5, 40.0, "idle"), # Idle Resource candidate
            ("gcp-cloudsql-analytics", "analytics-dw-replica", "Cloud SQL", "production", "us-central1", 58.0, 65.0, 300.0, "running"),
            ("gcp-bq-streaming-slot", "telemetry-pipeline", "BigQuery", "production", "us-central1", 82.0, 80.0, 600.0, "running"),
        ]
    }

    for item in configs.get(provider, []):
        r_id, r_name, service, env, region, cpu, mem, disk, status = item
        resources.append(
            ResourceMetricBase(
                provider=provider,
                service=service,
                resource_id=r_id,
                resource_name=r_name,
                environment=env,
                region=region,
                cpu_utilization_pct=cpu,
                memory_utilization_pct=mem,
                disk_utilization_gb=disk,
                network_in_mb=round(random.uniform(10.0, 500.0), 1),
                network_out_mb=round(random.uniform(15.0, 750.0), 1),
                status=status,
                timestamp=now
            )
        )

    return resources
