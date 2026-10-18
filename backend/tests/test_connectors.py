from datetime import date, timedelta
from backend.app.services.cloud.aws_connector import AWSConnector
from backend.app.services.cloud.azure_connector import AzureConnector
from backend.app.services.cloud.gcp_connector import GCPConnector


def test_aws_connector():
    connector = AWSConnector()
    status = connector.test_connection()
    assert status["connected"] is True
    
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    costs = connector.fetch_costs(start_date, end_date)
    assert len(costs) > 0
    assert all(c.provider == "AWS" for c in costs)
    
    metrics = connector.fetch_resource_metrics()
    assert len(metrics) > 0
    assert any(m.service == "EC2" for m in metrics)


def test_azure_connector():
    connector = AzureConnector()
    status = connector.test_connection()
    assert status["connected"] is True
    
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    costs = connector.fetch_costs(start_date, end_date)
    assert len(costs) > 0
    assert all(c.provider == "Azure" for c in costs)
    
    metrics = connector.fetch_resource_metrics()
    assert len(metrics) > 0


def test_gcp_connector():
    connector = GCPConnector()
    status = connector.test_connection()
    assert status["connected"] is True
    
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    costs = connector.fetch_costs(start_date, end_date)
    assert len(costs) > 0
    assert all(c.provider == "GCP" for c in costs)
    
    metrics = connector.fetch_resource_metrics()
    assert len(metrics) > 0
