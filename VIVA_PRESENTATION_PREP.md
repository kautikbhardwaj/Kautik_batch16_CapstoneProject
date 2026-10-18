# DevOps Dashboard — Viva & Presentation Defense Preparation

> Comprehensive guide for university viva panels, technical interviews, and stakeholder project presentations.

---

## 🎬 5-Minute Live Demonstration Walkthrough Script

Follow this structured step-by-step sequence during your project demonstration to maximize evaluation scoring:

### Minute 0:00 – 0:45 | Architecture & Problem Introduction
- **Action**: Open terminal, run `python run.py` (or show running Docker containers with `docker compose ps`).
- **Narrative**:
  > *"Good morning panel. Today we are presenting the DevOps Dashboard for Resource and Cost Monitoring across AWS, Azure, and GCP. Modern organizations face two critical challenges: fragmented cost visibility across disparate cloud billing consoles, and unchecked cloud waste from idle instances and orphaned disks. Our platform solves this by providing a unified, real-time FinOps and observability command center."*

### Minute 0:45 – 1:45 | Executive Overview & KPI Metrics
- **Action**: Open browser at `http://localhost:8000`. Point to the 5 top metric cards.
- **Narrative**:
  > *"At a glance, engineering leaders see:
  > 1. Month-to-Date Spend (\$4,218.40) with Month-over-Month change velocity.
  > 2. Linear Projected Run-rate (\$5,840.10) for end-of-month budget compliance.
  > 3. Algorithmic Potential Savings (\$595.50/mo) from automatically detected waste.
  > 4. Active Alert Incidents (3 active issues requiring immediate attention).
  > 5. 15 monitored multi-cloud assets with live idle indicators."*

### Minute 1:45 – 2:45 | Multi-Cloud Visualizations & Drill-Down
- **Action**: Show the interactive Daily Cost Trend chart and Provider Spend Doughnut.
- **Narrative**:
  > *"Notice the daily trend line. We can filter dynamically by cloud vendor (AWS, Azure, GCP), by environment (Production, Staging, Dev), or by date range. Notice the sudden cost spike in AWS RDS on October 15th — our anomaly engine caught an unindexed database query load that increased daily spend by 165%."*

### Minute 2:45 – 3:45 | FinOps Cost Optimization Hub (10% Evaluation Criteria)
- **Action**: Click on the **Cost Optimization** tab. Demonstrate the interactive **FinOps ROI Simulator**.
- **Narrative**:
  > *"Our FinOps engine automatically identifies multiple categories of cloud waste:
  > 1. Idle compute instances (CPU < 5%) such as forgotten development VMs.
  > 2. Oversized instances (5% - 20% CPU) ripe for rightsizing from 4xlarge to 2xlarge, saving \$110/mo each.
  > 3. Orphaned storage volumes (unattached EBS disks with 0 IOPS accruing storage charges).
  > 4. Unattached Elastic IPs and stale snapshots.
  > With our interactive simulator, stakeholders can project organizational ROI before applying changes."*

### Minute 3:45 – 4:30 | Alerting, Webhooks & Prometheus Observability
- **Action**: Switch to the **Alerts & Thresholds** tab. Click 'Test Slack' or 'Evaluate Rules Now'. Show `/metrics` in another tab.
- **Narrative**:
  > *"Our threshold engine monitors CPU > 85% and cost spike limits. We support native webhook dispatches to Slack and Microsoft Teams. Furthermore, for enterprise observability, our backend exposes standard Prometheus metrics at `/metrics` for scraping by Prometheus Alertmanager and pre-provisioned Grafana dashboards."*

### Minute 4:30 – 5:00 | Automated Tests & Conclusion
- **Action**: Switch to terminal and show `python -m pytest backend/tests/ -v` (13 passed tests) or run `python cli.py status`.
- **Narrative**:
  > *"The entire system is backed by 13 comprehensive unit and integration tests, an administrative CLI utility, and is fully containerized via Docker and Docker Compose. We are now open for questions from the panel."*

---

## ⚡ Terminal Command Quick-Reference Cheat Sheet

Keep these commands ready during the viva:

```bash
# 1. Run all automated tests
python -m pytest backend/tests/ -v

# 2. Launch the application locally
python run.py

# 3. Check administrative status via CLI
python cli.py status

# 4. Run statistical anomaly detection via CLI
python cli.py anomalies --threshold 2.0 --days 30

# 5. Run FinOps optimization recommendations via CLI
python cli.py optimize

# 6. Export cloud spend ledger to CSV
python cli.py export-csv --output current_ledger.csv

# 7. Start full microservice stack with Docker Compose
docker compose up -d
```

---

## ❓ Top 25 Technical Viva Questions & In-Depth Model Answers

### Category 1: Architecture & System Design

#### Q1: Why did you build a custom dashboard instead of using pure Grafana?
**Answer**:  
Grafana is an exceptional time-series visualization tool, but it is primarily a *passive* data viewer. Our custom dashboard is an **active FinOps operational portal**:
1. It supports stateful actions (e.g., creating custom alert rules in SQLite/PostgreSQL, marking recommendations as "Applied" or "Dismissed").
2. It executes custom Python business logic for anomaly detection, linear cost run-rate forecasting, and rightsizing calculations.
3. It retains Grafana compatibility by exposing a native Prometheus `/metrics` endpoint so enterprise teams can use both concurrently.

#### Q2: How did you solve the problem of divergent data models between AWS, Azure, and GCP?
**Answer**:  
We implemented an **Adapter / Connector design pattern**:
- AWS reports unblended/amortized daily cost line items.
- Azure returns pre-tax usage matrices grouped by ServiceName.
- GCP uses SKU-level billing exports and BigQuery tables.  
Our `CloudDataAggregator` ingests raw payloads from each vendor connector and maps them into a single unified relational schema (`CostRecord`: `provider`, `service`, `resource_id`, `environment`, `cost_usd`, `usage_amount`, `record_date`).

#### Q3: How does the application handle offline development or missing cloud credentials?
**Answer**:  
We built a dual-mode hybrid architecture:
- If real credentials (`AWS_ACCESS_KEY_ID`, `AZURE_SUBSCRIPTION_ID`, `GCP_PROJECT_ID`) are configured, the connectors call the official SDKs (`boto3`, `azure-mgmt-costmanagement`, `google-cloud-billing`).
- If credentials are absent or `MOCK_CLOUD_MODE=true` is set, the connectors gracefully fall back to a deterministic, high-fidelity multi-cloud sandbox generator. This allows evaluators, testers, and CI/CD pipelines to run full end-to-end demonstrations without incurring cloud API costs.

---

### Category 2: Data Aggregation & Persistence

#### Q4: What database is used and why?
**Answer**:  
We used SQLAlchemy ORM with a dual-database strategy:
1. **SQLite** for instant, zero-configuration local development.
2. **PostgreSQL 16** in production via Docker Compose for concurrent read/write scaling, robust indexing, and transaction isolation.

#### Q5: How do you prevent duplicate records during scheduled cloud syncs?
**Answer**:  
In `CloudDataAggregator.sync_all_clouds()`, before committing newly fetched cost records for a specific provider and date window, we execute an idempotent delete-then-insert within a single database transaction. This guarantees zero duplicate rows even if the sync job is triggered repeatedly.

---

### Category 3: FinOps & Cost Optimization (10% Evaluation Topic)

#### Q6: What are the mathematical rules used for idle instance detection?
**Answer**:  
An instance is flagged as idle if:
$$\text{Average CPU Utilization} < 5.0\% \quad \text{OR} \quad \text{Status} = \text{"idle"}$$
In non-production environments (Dev/Staging), instances running continuously with <5% CPU indicate forgotten workloads. We calculate potential savings at $90\%$ of the monthly compute charge upon scheduled shutdown.

#### Q7: How does your rightsizing recommendation engine work?
**Answer**:  
The engine checks if an instance's average CPU is between $5.0\%$ and $20.0\%$ and memory is under $35.0\%$. This proves the instance was over-provisioned. We recommend downsizing to the next smaller tier (e.g., 4xlarge to 2xlarge), yielding an immediate $50\%$ to $65\%$ cost reduction while preserving a $25\%$ safety headroom.

#### Q8: How are orphaned disks identified?
**Answer**:  
We look for storage volumes where:
$$\text{Disk Capacity} > 100\text{ GB} \quad \text{AND} \quad \text{CPU Utilization} = 0.0\%$$
When an EC2 or VM is terminated without deleting attached volumes, these disks accrue \$0.08–\$0.135 per GB-month indefinitely. Our engine flags them and calculates $100\%$ savings upon deletion after taking a compliance snapshot.

---

### Category 4: Analytics, Projections & Anomaly Detection

#### Q9: How is the end-of-month projected run-rate calculated?
**Answer**:  
We use linear velocity projection:
$$\text{Daily Velocity} = \frac{\text{Month-to-Date Spend}}{\text{Current Day of Month}}$$
$$\text{Projected Spend} = \text{MTD Spend} + (\text{Daily Velocity} \times \text{Days Remaining in Month})$$

#### Q10: How does your statistical Z-Score anomaly detection algorithm work?
**Answer**:  
Rather than static thresholds, we compute a rolling 7-day mean ($\mu$) and standard deviation ($\sigma$) for each cloud service. An anomaly is flagged if:
$$Z = \frac{\text{Actual Cost} - \mu}{\sigma} \ge 2.0$$
A Z-score $\ge 3.0$ indicates a critical spend surge with a statistical probability $< 0.13\%$, immediately firing a high-priority Slack webhook.

---

### Category 5: Observability, Alerting & Microservices

#### Q11: How does your alert evaluation engine avoid spamming notifications?
**Answer**:  
When a metric exceeds a threshold (e.g., CPU > 85%), before creating an incident and dispatching a webhook, the engine queries the `alert_incidents` table for any existing record for that specific `rule_id` and `resource_id` with `status == "active"`. If an active incident exists, it suppresses duplicate notifications until the previous incident is resolved.

#### Q12: How are Slack and Microsoft Teams alerts formatted?
**Answer**:  
In `NotificationDispatcher`, we construct JSON payloads conforming to Slack's Block Kit / Attachment schema and Microsoft Teams MessageCard schema, color-coding severity (Red for Critical, Yellow for Warning, Green for Info) and attaching metadata (Resource name, Provider, Current value vs Threshold).

#### Q13: What metrics are exported for Prometheus?
**Answer**:  
At `/metrics`, we expose:
- `cloud_cost_total_usd{provider, environment}` (Gauge)
- `cloud_resource_cpu_percent{provider, resource_name, environment}` (Gauge)
- `cloud_resource_memory_percent{provider, resource_name, environment}` (Gauge)
- `cloud_active_alerts_total{severity}` (Gauge)
- `cloud_potential_savings_usd{recommendation_type}` (Gauge)

#### Q14: How is Docker configured for this project?
**Answer**:  
We author a production `Dockerfile` for the FastAPI backend and static UI, and a `docker-compose.yml` orchestrating 5 interconnected microservices:
1. `app`: FastAPI backend on port 8000.
2. `db`: PostgreSQL 16 on port 5432 with volume persistence.
3. `prometheus`: Scraper on port 9090 scraping `app:8000/metrics`.
4. `alertmanager`: Alert routing on port 9093.
5. `grafana`: Visual analytics on port 3000 with auto-provisioned dashboards.

#### Q15: What is tested in your test suite?
**Answer**:  
We built 13 Pytest tests covering:
- AWS, Azure, and GCP connector contracts and data generation.
- Database ingestion and deduplication.
- FinOps optimization engine savings calculations.
- Statistical Z-Score anomaly detector.
- Alert rules evaluation and incident creation.
- REST API endpoints (`/healthz`, `/metrics`, `/api/dashboard/overview`, `/api/costs/records`, `/api/resources`, `/api/alerts/rules`, `/api/recommendations`, `/api/sync/status`).
All 13 tests pass cleanly with 100% success rate.
