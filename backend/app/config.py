import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "DevOps Multi-Cloud Cost & Resource Dashboard"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./devops_costs.db"

    # Multi-Cloud Mode: if True, gracefully generates synthetic live/historical data
    # when actual credentials are absent or during sandbox demos
    MOCK_CLOUD_MODE: bool = True
    SYNC_INTERVAL_HOURS: int = 24

    # AWS Credentials
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_DEFAULT_REGION: str = "us-east-1"

    # Azure Credentials
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_SUBSCRIPTION_ID: Optional[str] = None

    # GCP Credentials
    GCP_PROJECT_ID: Optional[str] = None
    GCP_BILLING_ACCOUNT_ID: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # Alerting & Notifications
    SLACK_WEBHOOK_URL: Optional[str] = None
    TEAMS_WEBHOOK_URL: Optional[str] = None
    ALERTMANAGER_URL: str = "http://localhost:9093"

    # Thresholds
    DAILY_COST_SPIKE_THRESHOLD_PCT: float = 25.0
    MONTHLY_BUDGET_LIMIT_USD: float = 10000.0
    HIGH_CPU_THRESHOLD_PCT: float = 85.0
    IDLE_CPU_THRESHOLD_PCT: float = 5.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
