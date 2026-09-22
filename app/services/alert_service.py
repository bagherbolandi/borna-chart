from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.workflow import Alert


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        alert_code: str,
        related_object_type: str,
        related_object_id: int,
        alert_type: str,
        severity: str,
        owner: str | None,
        financial_impact: float = 0,
        created_by: str | None = None,
        message: str | None = None,
        escalation_level: int = 0,
    ) -> Alert:
        alert = Alert(
            alert_code=alert_code,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            alert_type=alert_type,
            severity=severity,
            owner=owner,
            message=message,
            escalation_level=escalation_level,
            financial_impact=Decimal(str(financial_impact)),
            status="open",
            created_by=created_by,
            modified_by=created_by,
        )
        self.db.add(alert)
        self.db.flush()
        return alert

    def list_alerts(self, *, owner: str | None = None, status: str | None = None) -> list[Alert]:
        query = self.db.query(Alert)
        if owner:
            query = query.filter(Alert.owner == owner)
        if status:
            query = query.filter(Alert.status == status)
        return query.order_by(Alert.id.desc()).all()

    def resolve_for_object(self, *, related_object_type: str, related_object_id: int) -> int:
        alerts = (
            self.db.query(Alert)
            .filter(
                Alert.related_object_type == related_object_type,
                Alert.related_object_id == related_object_id,
                Alert.status == "open",
            )
            .all()
        )
        for alert in alerts:
            alert.status = "resolved"
        self.db.flush()
        return len(alerts)

    def exists_open_alert(self, *, alert_code: str, related_object_type: str, related_object_id: int) -> bool:
        return (
            self.db.query(Alert)
            .filter(
                Alert.alert_code == alert_code,
                Alert.related_object_type == related_object_type,
                Alert.related_object_id == related_object_id,
                Alert.status == "open",
            )
            .first()
            is not None
        )
