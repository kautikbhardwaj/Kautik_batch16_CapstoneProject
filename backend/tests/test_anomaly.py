from backend.app.database import SessionLocal
from backend.app.services.anomaly import AnomalyDetectionEngine


def test_anomaly_detection_engine():
    db = SessionLocal()
    try:
        anomalies = AnomalyDetectionEngine.calculate_cost_anomalies(db, z_threshold=1.5, days_lookback=30)
        assert isinstance(anomalies, list)
        if len(anomalies) > 0:
            first = anomalies[0]
            assert "provider" in first
            assert "service" in first
            assert "z_score" in first
            assert "percent_spike" in first
            assert first["z_score"] >= 1.5
    finally:
        db.close()
