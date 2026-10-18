from typing import Dict
from backend.app.services.cloud.base import BaseCloudConnector
from backend.app.services.cloud.aws_connector import AWSConnector
from backend.app.services.cloud.azure_connector import AzureConnector
from backend.app.services.cloud.gcp_connector import GCPConnector

_connectors: Dict[str, BaseCloudConnector] = {}


def get_cloud_connectors() -> Dict[str, BaseCloudConnector]:
    global _connectors
    if not _connectors:
        _connectors = {
            "AWS": AWSConnector(),
            "Azure": AzureConnector(),
            "GCP": GCPConnector(),
        }
    return _connectors


def get_connector(provider: str) -> BaseCloudConnector:
    connectors = get_cloud_connectors()
    if provider not in connectors:
        raise ValueError(f"Unsupported cloud provider: {provider}. Supported: {list(connectors.keys())}")
    return connectors[provider]
