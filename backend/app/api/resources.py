from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models import ResourceMetric
from backend.app.schemas import ResourceMetricResponse

router = APIRouter(prefix="/resources", tags=["Resource Monitoring"])


@router.get("", response_model=List[ResourceMetricResponse])
def get_resources(
    provider: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    status: Optional[str] = Query(None), # running, idle, stopped
    min_cpu: Optional[float] = Query(None),
    max_cpu: Optional[float] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(ResourceMetric)
    if provider and provider != "ALL":
        query = query.filter(ResourceMetric.provider == provider)
    if environment and environment != "ALL":
        query = query.filter(ResourceMetric.environment == environment)
    if status and status != "ALL":
        query = query.filter(ResourceMetric.status == status)
    if min_cpu is not None:
        query = query.filter(ResourceMetric.cpu_utilization_pct >= min_cpu)
    if max_cpu is not None:
        query = query.filter(ResourceMetric.cpu_utilization_pct <= max_cpu)

    return query.order_by(ResourceMetric.cpu_utilization_pct.desc()).limit(limit).all()


@router.get("/{resource_id}", response_model=ResourceMetricResponse)
def get_resource_detail(resource_id: str, db: Session = Depends(get_db)):
    res = db.query(ResourceMetric).filter(ResourceMetric.resource_id == resource_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")
    return res
