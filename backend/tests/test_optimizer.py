import pytest
from backend.app.database import SessionLocal
from backend.app.services.optimizer import CostOptimizationEngine
from backend.app.models import CostRecommendation


def test_cost_optimization_engine():
    db = SessionLocal()
    try:
        recs = CostOptimizationEngine.evaluate_optimizations(db)
        assert isinstance(recs, list)
        
        # Verify total savings
        savings = CostOptimizationEngine.get_total_potential_savings(db)
        assert savings > 0.0
        
        # Check recommendation types
        types = [r.recommendation_type for r in db.query(CostRecommendation).all()]
        assert "idle_resource" in types
        assert "rightsizing" in types
        assert "unattached_storage" in types
    finally:
        db.close()
