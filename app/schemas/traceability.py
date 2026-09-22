from pydantic import BaseModel

from app.schemas.alert import AlertRead
from app.schemas.approval import ApprovalRead


class TraceabilityDocument(BaseModel):
    object_type: str
    object_id: int
    relation: str
    code: str
    status: str | None = None
    workflow_instance_id: int | None = None
    current_state: str | None = None
    current_owner: str | None = None
    current_role: str | None = None
    due_at: str | None = None
    escalation_level: int = 0
    financial_impact: float = 0
    amount: float | None = None
    currency: str | None = None


class TraceabilityOverview(BaseModel):
    process_name: str
    root_object_type: str
    root_object_id: int
    root_code: str
    root_status: str | None = None
    active_object_type: str | None = None
    active_object_id: int | None = None
    active_object_code: str | None = None
    current_owner: str | None = None
    current_role: str | None = None
    current_state: str | None = None
    due_at: str | None = None
    escalation_level: int = 0
    is_overdue: bool = False
    financial_impact: float = 0
    open_alerts: int = 0
    linked_document_count: int = 0


class TraceabilityTimelineEvent(BaseModel):
    event_time: str
    source_type: str
    source_id: int | None = None
    source_code: str | None = None
    event_type: str
    actor: str | None = None
    status: str | None = None
    message: str | None = None


class TraceabilityResponse(BaseModel):
    overview: TraceabilityOverview
    linked_documents: list[TraceabilityDocument]
    approvals: list[ApprovalRead]
    alerts: list[AlertRead]
    timeline: list[TraceabilityTimelineEvent]
