from datetime import datetime

from app.schemas.common import ORMModel


class AlertRead(ORMModel):
    id: int
    alert_code: str
    related_object_type: str
    related_object_id: int
    alert_type: str
    severity: str
    owner: str | None
    message: str | None
    escalation_level: int
    financial_impact: float
    status: str
    created_at: datetime | None = None


class SchedulerRunResult(ORMModel):
    scanned_instances: int
    overdue_instances: int
    escalated_instances: int
    resolved_alerts: int
    created_alerts: int
