from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db, SessionLocal
from backend.app.models import ProviderStatus
from backend.app.schemas import ProviderSyncStatusResponse
from backend.app.services.aggregator import CloudDataAggregator
from backend.app.services.optimizer import CostOptimizationEngine
from backend.app.services.alerting import AlertEngine

router = APIRouter(prefix="/sync", tags=["Cloud Synchronization"])


def background_sync_task():
    db = SessionLocal()
    try:
        CloudDataAggregator.sync_all_clouds(db, days_back=30)
        CostOptimizationEngine.evaluate_optimizations(db)
        # Note: evaluate_rules is async so it will run or be scheduled
    finally:
        db.close()


@router.post("/trigger")
def trigger_sync(background_tasks: BackgroundTasks, days: int = Query(30, ge=1, le=90), db: Session = Depends(get_db)):
    # Synchronously run or dispatch
    result = CloudDataAggregator.sync_all_clouds(db, days_back=days)
    CostOptimizationEngine.evaluate_optimizations(db)
    return {"message": "Cloud sync completed successfully", "details": result}


@router.get("/status", response_model=List[ProviderSyncStatusResponse])
def get_sync_status(db: Session = Depends(get_db)):
    statuses = db.query(ProviderStatus).all()
    return statuses
