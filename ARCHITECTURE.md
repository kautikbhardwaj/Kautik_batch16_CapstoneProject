# Technical Architecture & System Design Document

## 1. Executive Architecture Summary

The **DevOps Multi-Cloud Resource & Cost Monitoring Platform** is engineered as a decoupled, microservice-ready system designed to solve the challenges of fragmented multi-cloud cost visibility, resource sprawl, and untracked infrastructure waste across **AWS**, **Microsoft Azure**, and **Google Cloud Platform (GCP)**.

```mermaid
graph TD
    subgraph MultiCloudIngestion ["Cloud Providers & Ingestion Layer"]
        AWS_API["AWS Cost Explorer API<br/>AWS CloudWatch Metrics"]
        AZURE_API["Azure Cost Management API<br/>Azure Monitor Metrics"]
        GCP_API["GCP Cloud Billing API<br/>Cloud Monitoring API"]
        MOCK_GEN["Multi-Cloud Sandbox Generator<br/>(Graceful Fallback / Demo Mode)"]
    end

    subgraph CoreApplication ["FastAPI Backend Engine"]
        Connectors["Provider Connectors<br/>(AWS, Azure, GCP)"]
        Aggregator["Data Normalization & Ingestion Engine"]
        Analytics["Analytics & Run-Rate Engine"]
        Optimizer["FinOps Waste Detection Engine"]
        AlertEngine["Threshold & Incident Evaluator"]
        PrometheusExporter["Prometheus Metrics Service (/metrics)"]
    end

    subgraph Storage ["Relational Data Store"]
        DB[(PostgreSQL / SQLite)]
    end

    subgraph Observability ["Observability & Notification Stack"]
        Prometheus["Prometheus Server :9090"]
        Alertmanager["Prometheus Alertmanager :9093"]
        Slack["Slack & Microsoft Teams Webhooks"]
        Grafana["Grafana 10.4 Visualization"]
        WebUI["Interactive Web Dashboard"]
    end

    AWS_API --> Connectors
    AZURE_API --> Connectors
    GCP_API --> Connectors
    MOCK_GEN --> Connectors

    Connectors --> Aggregator
    Aggregator --> DB
    DB --> Analytics
    DB --> Optimizer
    DB --> AlertEngine
    DB --> PrometheusExporter

    Analytics --> WebUI
    Optimizer --> WebUI
    AlertEngine --> WebUI
    AlertEngine --> Slack

    PrometheusExporter --> Prometheus
    Prometheus --> Alertmanager
    Prometheus --> Grafana
    Alertmanager --> Slack
```

---

## 2. Ingestion & Data Normalization Layer

Different cloud providers structure cost and usage data in divergent formats:
- **AWS**: Uses `UnblendedCost`, `BlendedCost`, or `AmortizedCost` grouped by `DIMENSION: SERVICE` or `TAGS`.
- **Azure**: Uses `PreTaxCost` query payloads grouped by `Dimension: ServiceName`.
- **GCP**: Exposes SKU-level billing records, usage quantities in milli-cores or gibibyte-months, and BigQuery export datasets.

### Unified Relational Schema

To provide cross-cloud queryability, the Aggregator translates all external inputs into standardized internal models:

```mermaid
erDiagram
    COST_RECORD {
        int id PK
        string provider
        string service
        string resource_id
        string environment
        string region
        float cost_usd
        float usage_amount
        string usage_unit
        date record_date
        datetime created_at
        json tags
    }

    RESOURCE_METRIC {
        int id PK
        string provider
        string service
        string resource_id
        string resource_name
        string environment
        string region
        float cpu_utilization_pct
        float memory_utilization_pct
        float disk_utilization_gb
        float network_in_mb
        float network_out_mb
        string status
        datetime timestamp
    }

    ALERT_RULE {
        int id PK
        string name
        string metric_type
        string provider
        string environment
        float threshold_value
        string operator
        string severity
        string notification_channel
        string webhook_url
        boolean enabled
        datetime created_at
    }

    ALERT_INCIDENT {
        int id PK
        int rule_id FK
        string title
        text message
        string provider
        string service
        string resource_id
        string metric_type
        float current_value
        float threshold_value
        string severity
        string status
        datetime triggered_at
        datetime resolved_at
    }

    COST_RECOMMENDATION {
        int id PK
        string provider
        string service
        string resource_id
        string resource_name
        string recommendation_type
        string title
        text description
        float current_monthly_cost
        float estimated_monthly_savings
        string status
        text action_plan
        datetime detected_at
    }

    PROVIDER_STATUS {
        int id PK
        string provider UK
        string status
        datetime last_sync_at
        string message
        int records_synced
    }

    ALERT_RULE ||--o{ ALERT_INCIDENT : triggers
```

---

## 3. FinOps Cost Optimization Engine

The optimization engine executes automated algorithms over resource metrics and cost records to surface high-impact cost savings:

### 1. Idle Resource Detection Algorithm
$$\text{Average CPU} < 5.0\% \quad \text{OR} \quad \text{Status} = \text{"idle"}$$
- Flags forgotten development/staging instances running continuously during weekends and nights.
- Calculates estimated savings: $90\%$ of total monthly compute charge upon scheduled shutdown or termination.

### 2. Compute Rightsizing Algorithm
$$5.0\% \le \text{Average CPU} \le 20.0\% \quad \text{AND} \quad \text{Memory} < 30.0\%$$
- Identifies over-provisioned instance tiers (e.g., `m5.4xlarge` provisioned for a light steady-state service).
- Recommends downsizing to the next smaller tier (e.g., `m5.xlarge`), projecting a $55\% \text{ to } 65\%$ reduction in baseline hourly costs while maintaining safety headroom.

### 3. Orphaned Storage Detection Algorithm
$$\text{Disk Capacity} > 100\text{ GB} \quad \text{AND} \quad \text{CPU Utilization} = 0.0\%$$
- Detects unattached EBS volumes, unmanaged Azure Disks, and persistent GCP disks detached from terminated VMs.
- Recommends taking a point-in-time compliance snapshot and deleting the unattached block device.

---

## 4. Alerting & Notification Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as Background Scheduler
    participant Engine as Alert Engine
    participant DB as Relational DB
    participant Dispatcher as Notification Dispatcher
    participant Slack as Slack / Teams Webhook
    participant Prom as Prometheus Alertmanager

    Scheduler->>Engine: Trigger Rule Evaluation
    Engine->>DB: Query Active Rules (enabled = true)
    Engine->>DB: Query Metrics (CPU, RAM, Daily Costs)
    loop For Each Rule
        alt Metric exceeds Threshold
            Engine->>DB: Check for Active Unresolved Incident
            alt Incident Does Not Exist
                Engine->>DB: Insert Alert Incident (status = active)
                Engine->>Dispatcher: Send Notification Payload
                Dispatcher->>Slack: HTTP POST JSON Webhook
                Dispatcher->>Prom: Expose Gauge to /metrics
            end
        end
    end
```

---

## 5. Security & Least Privilege Architecture

1. **Read-Only IAM Policies**: Cloud connectors operate exclusively under least-privilege read-only permissions (`ce:GetCostAndUsage`, `monitoring:GetMetricData`, `CostManagement.Reader`). No destructive write permissions are required.
2. **Zero Plaintext Tokens**: Application Default Credentials (ADC) or environmental secrets are loaded via environment variables; credentials are never committed or exposed in frontend payloads.
3. **Graceful Simulation Fallback**: If cloud credentials are not supplied, the platform automatically engages its sandboxed multi-cloud engine, ensuring full evaluation capabilities without security exposure.
