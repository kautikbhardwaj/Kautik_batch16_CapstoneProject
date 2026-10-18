import math
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import CostRecord


class AnomalyDetectionEngine:
    """
    Statistical Anomaly Detection Engine for Multi-Cloud Cost Spikes.
    Uses 7-day rolling window moving average and standard deviation (Z-score calculation)
    to detect abnormal cost surges caused by runaway jobs, unindexed queries, or memory leaks.
    """

    @staticmethod
    def calculate_cost_anomalies(
        db: Session,
        z_threshold: float = 2.0,
        days_lookback: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Scans daily spend records per provider and service.
        A cost is flagged as an anomaly if:
            Z = (current_cost - rolling_mean) / rolling_std > z_threshold
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_lookback + 7)

        # Query all costs grouped by date, provider, service
        rows = db.query(
            CostRecord.record_date,
            CostRecord.provider,
            CostRecord.service,
            func.sum(CostRecord.cost_usd).label("daily_sum")
        ).filter(
            CostRecord.record_date >= start_date,
            CostRecord.record_date <= end_date
        ).group_by(
            CostRecord.record_date,
            CostRecord.provider,
            CostRecord.service
        ).order_by(CostRecord.record_date.asc()).all()

        # Organize by (provider, service) -> list of (date, cost)
        series_map: Dict[tuple, List[tuple]] = {}
        for r_date, provider, service, daily_sum in rows:
            key = (provider, service)
            if key not in series_map:
                series_map[key] = []
            series_map[key].append((r_date, float(daily_sum or 0.0)))

        anomalies = []

        # Analyze each time series with a rolling 7-day baseline window
        for (provider, service), time_series in series_map.items():
            if len(time_series) < 8:
                continue

            for i in range(7, len(time_series)):
                window = [cost for _, cost in time_series[i - 7:i]]
                target_date, target_cost = time_series[i]

                mean = sum(window) / len(window)
                variance = sum((x - mean) ** 2 for x in window) / len(window)
                std_dev = math.sqrt(variance)

                if std_dev > 0:
                    z_score = (target_cost - mean) / std_dev
                else:
                    z_score = 0.0

                pct_increase = ((target_cost - mean) / mean * 100) if mean > 0 else 0.0

                if z_score >= z_threshold and target_cost > 50.0:
                    anomalies.append({
                        "date": target_date.strftime("%Y-%m-%d"),
                        "provider": provider,
                        "service": service,
                        "actual_cost": round(target_cost, 2),
                        "expected_baseline": round(mean, 2),
                        "z_score": round(z_score, 2),
                        "percent_spike": round(pct_increase, 1),
                        "severity": "critical" if z_score >= 3.0 else "warning",
                        "root_cause_hypothesis": (
                            f"Sudden {pct_increase:.1f}% spend surge over 7-day baseline (${mean:.2f}). "
                            f"Likely unindexed queries, unexpected scale-out event, or orphaned background batch."
                        )
                    })

        return sorted(anomalies, key=lambda x: x["z_score"], reverse=True)
