from app.schemas.common import ORMModel


class ApprovalRead(ORMModel):
    id: int
    object_type: str
    object_id: int
    approval_stage: str
    approver_name: str
    approver_role: str
    decision: str
    decision_note: str | None
    decided_at: str
