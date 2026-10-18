from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_healthcheck():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_prometheus_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "cloud_cost_total_usd" in response.text


def test_dashboard_overview():
    response = client.get("/api/dashboard/overview?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "total_spend_month_to_date" in data
    assert "projected_spend_month_end" in data
    assert "provider_breakdown" in data
    assert len(data["provider_breakdown"]) > 0


def test_cost_records_api():
    response = client.get("/api/costs/records?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10


def test_resources_api():
    response = client.get("/api/resources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_alerts_api():
    # List rules
    rules_res = client.get("/api/alerts/rules")
    assert rules_res.status_code == 200
    assert len(rules_res.json()) > 0

    # List incidents
    inc_res = client.get("/api/alerts/incidents")
    assert inc_res.status_code == 200


def test_recommendations_api():
    recs_res = client.get("/api/recommendations")
    assert recs_res.status_code == 200
    assert isinstance(recs_res.json(), list)


def test_sync_status_api():
    status_res = client.get("/api/sync/status")
    assert status_res.status_code == 200
    assert isinstance(status_res.json(), list)
