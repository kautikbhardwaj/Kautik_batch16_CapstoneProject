from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from backend.app.database import get_db
from backend.app.models import AlertRule, AlertIncident
from backend.app.schemas import (
    AlertRuleBase,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertIncidentResponse
)
from backend.app.services.alerting import AlertEngine
from backend.app.services.notifier import NotificationDispatcher

router = APIRouter(prefix="/alerts", tags=["Alerting & Notifications"])


@router.get("/rules", response_model=List[AlertRuleResponse])
def get_alert_rules(db: Session = Depends(get_db)):
    return db.query(AlertRule).order_by(AlertRule.id.asc()).all()


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
def create_alert_rule(rule_in: AlertRuleCreate, db: Session = Depends(get_db)):
    rule = AlertRule(**rule_in.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(rule_id: int, rule_in: AlertRuleCreate, db: Session = Depends(get_db)):
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    for k, v in rule_in.model_dump().items():
        setattr(rule, k, v)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    db.delete(rule)
    db.commit()
    return {"message": f"Rule {rule_id} successfully deleted"}


@router.get("/incidents", response_model=List[AlertIncidentResponse])
def get_alert_incidents(
    status: Optional[str] = Query(None), # active, acknowledged, resolved
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(AlertIncident)
    if status and status != "ALL":
        query = query.filter(AlertIncident.status == status)
    if severity and severity != "ALL":
        query = query.filter(AlertIncident.severity == severity)
    return query.order_by(AlertIncident.triggered_at.desc()).limit(limit).all()


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(
    incident_id: int,
    status_update: str = Query("resolved", pattern="^(acknowledged|resolved)$"),
    db: Session = Depends(get_db)
):
    inc = db.query(AlertIncident).filter(AlertIncident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc.status = status_update
    if status_update == "resolved":
        inc.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": f"Incident {incident_id} marked as {status_update}"}


@router.post("/evaluate")
async def trigger_evaluation(db: Session = Depends(get_db)):
    new_incidents = await AlertEngine.evaluate_rules(db)
    return {
        "status": "success",
        "incidents_evaluated": len(new_incidents),
        "new_incidents": [
            {"id": i.id, "title": i.title, "severity": i.severity}
            for i in new_incidents
        ]
    }


@router.post("/test-notification")
async def test_notification(
    channel: str = Body("slack", embed=True),
    webhook_url: Optional[str] = Body(None, embed=True)
):
    success = False
    if channel.lower() == "teams":
        success = await NotificationDispatcher.send_teams_alert(
            webhook_url=webhook_url,
            title="[Test Alert] Cloud Budget Threshold",
            message="This is a test notification from DevOps Cost & Resource Monitor.",
            severity="warning"
        )
    else:
        success = await NotificationDispatcher.send_slack_alert(
            webhook_url=webhook_url,
            title="[Test Alert] Multi-Cloud Cost Anomaly",
            message="Test alert: AWS RDS daily spend spiked by 180% over 7-day average.",
            severity="critical",
            metadata={"Provider": "AWS", "Environment": "Production", "Current Cost": "$248.50"}
        )

    return {"status": "success" if success else "failed", "simulated": webhook_url is None}
