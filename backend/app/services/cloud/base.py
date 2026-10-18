from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Any
from backend.app.schemas import CostRecordBase, ResourceMetricBase


class BaseCloudConnector(ABC):
    """
    Abstract Base Class for Multi-Cloud Connectors (AWS, Azure, GCP).
    Provides standard interfaces for cost and resource metric aggregation.
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Verify credentials and API access for this cloud provider.
        Returns a dict with {"connected": bool, "mode": "live" | "mock", "message": str}
        """
        pass

    @abstractmethod
    def fetch_costs(self, start_date: date, end_date: date) -> List[CostRecordBase]:
        """
        Fetch normalized daily cost records for the specified date range.
        """
        pass

    @abstractmethod
    def fetch_resource_metrics(self) -> List[ResourceMetricBase]:
        """
        Fetch real-time utilization metrics (CPU, RAM, Disk, Network)
        for resources managed under this provider.
        """
        pass
