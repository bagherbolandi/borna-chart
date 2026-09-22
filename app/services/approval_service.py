from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.workflow import Approval


class ApprovalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        object_type: str,
        object_id: int,
        approval_stage: str,
        approver_name: str,
        approver_role: str,
        decision: str,
        decision_note: str | None = None,
    ) -> Approval:
        approval = Approval(
            object_type=object_type,
            object_id=object_id,
            approval_stage=approval_stage,
            approver_name=approver_name,
            approver_role=approver_role,
            decision=decision,
            decision_note=decision_note,
            decided_at=datetime.now(UTC).isoformat(),
            created_by=approver_name,
            modified_by=approver_name,
        )
        self.db.add(approval)
        self.db.flush()
        return approval

    def list_for_object(self, object_type: str, object_id: int) -> list[Approval]:
        return (
            self.db.query(Approval)
            .filter(Approval.object_type == object_type, Approval.object_id == object_id)
            .order_by(Approval.id.asc())
            .all()
        )
