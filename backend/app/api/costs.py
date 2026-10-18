from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from backend.app.database import get_db
from backend.app.models import CostRecord
from backend.app.schemas import CostRecordResponse, DailyCostPoint, ServiceSpend, ProviderSpend
from backend.app.services.analytics import CloudAnalyticsEngine

router = APIRouter(prefix="/costs", tags=["Cost Monitoring"])


@router.get("/records", response_model=List[CostRecordResponse])
def get_cost_records(
    provider: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(CostRecord)
    if provider and provider != "ALL":
        query = query.filter(CostRecord.provider == provider)
    if environment and environment != "ALL":
        query = query.filter(CostRecord.environment == environment)
    if service and service != "ALL":
        query = query.filter(CostRecord.service.ilike(f"%{service}%"))
    if start_date:
        query = query.filter(CostRecord.record_date >= start_date)
    if end_date:
        query = query.filter(CostRecord.record_date <= end_date)

    return query.order_by(CostRecord.record_date.desc(), CostRecord.cost_usd.desc())\
                .offset(offset).limit(limit).all()


@router.get("/trend", response_model=List[DailyCostPoint])
def get_cost_trend(
    provider: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return CloudAnalyticsEngine.get_daily_trend(
        db, start_date=start_date, end_date=end_date, provider=provider, environment=environment
    )


@router.get("/by-service", response_model=List[ServiceSpend])
def get_cost_by_service(
    provider: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    days: int = Query(30, ge=7, le=90),
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db)
):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return CloudAnalyticsEngine.get_top_services(
        db, limit=limit, start_date=start_date, end_date=end_date, provider=provider, environment=environment
    )


@router.get("/by-provider", response_model=List[ProviderSpend])
def get_cost_by_provider(
    environment: Optional[str] = Query(None),
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return CloudAnalyticsEngine.get_provider_breakdown(
        db, start_date=start_date, end_date=end_date, environment=environment
    )
