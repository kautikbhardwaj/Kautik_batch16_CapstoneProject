from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models import CostRecommendation
from backend.app.schemas import CostRecommendationResponse
from backend.app.services.optimizer import CostOptimizationEngine

router = APIRouter(prefix="/recommendations", tags=["Cost Optimization"])


@router.get("", response_model=List[CostRecommendationResponse])
def get_recommendations(
    provider: Optional[str] = Query(None),
    recommendation_type: Optional[str] = Query(None),
    status: Optional[str] = Query("pending"),
    db: Session = Depends(get_db)
):
    query = db.query(CostRecommendation)
    if provider and provider != "ALL":
        query = query.filter(CostRecommendation.provider == provider)
    if recommendation_type and recommendation_type != "ALL":
        query = query.filter(CostRecommendation.recommendation_type == recommendation_type)
    if status and status != "ALL":
        query = query.filter(CostRecommendation.status == status)

    return query.order_by(CostRecommendation.estimated_monthly_savings.desc()).all()


@router.post("/{rec_id}/status")
def update_recommendation_status(
    rec_id: int,
    status: str = Query(..., pattern="^(pending|applied|dismissed)$"),
    db: Session = Depends(get_db)
):
    rec = db.query(CostRecommendation).filter(CostRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.status = status
    db.commit()
    return {"message": f"Recommendation {rec_id} status updated to {status}"}


@router.post("/refresh")
def refresh_recommendations(db: Session = Depends(get_db)):
    recs = CostOptimizationEngine.evaluate_optimizations(db)
    return {
        "status": "success",
        "new_recommendations_count": len(recs),
        "total_savings_identified": CostOptimizationEngine.get_total_potential_savings(db)
    }
