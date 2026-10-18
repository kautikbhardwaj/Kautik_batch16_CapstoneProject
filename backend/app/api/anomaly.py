from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import get_db
from backend.app.services.anomaly import AnomalyDetectionEngine

router = APIRouter(prefix="/anomalies", tags=["Cost Anomalies"])


@router.get("", response_model=List[Dict[str, Any]])
def get_cost_anomalies(
    z_threshold: float = Query(2.0, ge=1.0, le=5.0, description="Z-score anomaly threshold"),
    days: int = Query(30, ge=7, le=90, description="Days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Returns detected multi-cloud cost anomalies using statistical Z-Score
    and 7-day rolling window baseline calculation.
    """
    return AnomalyDetectionEngine.calculate_cost_anomalies(
        db, z_threshold=z_threshold, days_lookback=days
    )
