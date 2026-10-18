from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import CostRecord
from backend.app.schemas import DailyCostPoint, ProviderSpend, ServiceSpend


class CloudAnalyticsEngine:
    @staticmethod
    def get_daily_trend(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
        environment: Optional[str] = None
    ) -> List[DailyCostPoint]:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        query = db.query(
            CostRecord.record_date,
            CostRecord.provider,
            func.sum(CostRecord.cost_usd).label("daily_cost")
        ).filter(
            CostRecord.record_date >= start_date,
            CostRecord.record_date <= end_date
        )

        if provider and provider != "ALL":
            query = query.filter(CostRecord.provider == provider)
        if environment and environment != "ALL":
            query = query.filter(CostRecord.environment == environment)

        rows = query.group_by(CostRecord.record_date, CostRecord.provider).order_by(CostRecord.record_date).all()

        # Build chronological map
        date_map: Dict[str, Dict[str, float]] = {}
        curr = start_date
        while curr <= end_date:
            d_str = curr.strftime("%Y-%m-%d")
            date_map[d_str] = {"AWS": 0.0, "Azure": 0.0, "GCP": 0.0, "total": 0.0}
            curr += timedelta(days=1)

        for record_date, p_name, daily_cost in rows:
            d_str = record_date.strftime("%Y-%m-%d")
            if d_str in date_map and p_name in date_map[d_str]:
                cost = round(float(daily_cost or 0.0), 2)
                date_map[d_str][p_name] = cost
                date_map[d_str]["total"] = round(date_map[d_str]["total"] + cost, 2)

        return [
            DailyCostPoint(
                date=k,
                AWS=v["AWS"],
                Azure=v["Azure"],
                GCP=v["GCP"],
                total=v["total"]
            )
            for k, v in sorted(date_map.items())
        ]

    @staticmethod
    def get_provider_breakdown(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        environment: Optional[str] = None
    ) -> List[ProviderSpend]:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        query = db.query(
            CostRecord.provider,
            func.sum(CostRecord.cost_usd).label("total_cost"),
            func.count(func.distinct(CostRecord.service)).label("service_count")
        ).filter(
            CostRecord.record_date >= start_date,
            CostRecord.record_date <= end_date
        )

        if environment and environment != "ALL":
            query = query.filter(CostRecord.environment == environment)

        rows = query.group_by(CostRecord.provider).all()
        grand_total = sum(float(r[1] or 0.0) for r in rows) or 1.0

        result = []
        for p, total, count in rows:
            cost = float(total or 0.0)
            result.append(
                ProviderSpend(
                    provider=p,
                    total_cost=round(cost, 2),
                    percentage=round((cost / grand_total) * 100, 1),
                    services_count=int(count or 0)
                )
            )
        return result

    @staticmethod
    def get_top_services(
        db: Session,
        limit: int = 8,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
        environment: Optional[str] = None
    ) -> List[ServiceSpend]:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        query = db.query(
            CostRecord.service,
            CostRecord.provider,
            func.sum(CostRecord.cost_usd).label("service_total")
        ).filter(
            CostRecord.record_date >= start_date,
            CostRecord.record_date <= end_date
        )

        if provider and provider != "ALL":
            query = query.filter(CostRecord.provider == provider)
        if environment and environment != "ALL":
            query = query.filter(CostRecord.environment == environment)

        rows = query.group_by(CostRecord.service, CostRecord.provider)\
                    .order_by(func.sum(CostRecord.cost_usd).desc())\
                    .limit(limit).all()

        return [
            ServiceSpend(
                service=r[0],
                provider=r[1],
                total_cost=round(float(r[2] or 0.0), 2)
            )
            for r in rows
        ]

    @staticmethod
    def calculate_run_rate_and_mom(db: Session) -> Dict[str, float]:
        today = date.today()
        # Current 30 days
        cur_start = today - timedelta(days=30)
        cur_cost = db.query(func.sum(CostRecord.cost_usd))\
                     .filter(CostRecord.record_date >= cur_start, CostRecord.record_date <= today)\
                     .scalar() or 0.0

        # Prior 30 days
        prev_start = cur_start - timedelta(days=30)
        prev_end = cur_start - timedelta(days=1)
        prev_cost = db.query(func.sum(CostRecord.cost_usd))\
                      .filter(CostRecord.record_date >= prev_start, CostRecord.record_date <= prev_end)\
                      .scalar() or 0.0

        mom_change_pct = 0.0
        if prev_cost > 0:
            mom_change_pct = round(((cur_cost - prev_cost) / prev_cost) * 100, 2)

        # Projected end of month calculation
        days_in_current_month = 30
        current_day_of_month = max(today.day, 1)
        # Average daily spend in current month
        month_start = today.replace(day=1)
        mtd_spend = db.query(func.sum(CostRecord.cost_usd))\
                      .filter(CostRecord.record_date >= month_start, CostRecord.record_date <= today)\
                      .scalar() or cur_cost * (current_day_of_month / 30.0)

        daily_avg = mtd_spend / current_day_of_month
        projected = mtd_spend + (daily_avg * (days_in_current_month - current_day_of_month))

        return {
            "month_to_date": round(float(mtd_spend), 2),
            "projected_month_end": round(float(projected), 2),
            "mom_change_pct": mom_change_pct
        }
