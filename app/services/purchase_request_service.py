from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.procurement import PurchaseRequest, PurchaseRequestLine
from app.models.workflow import WorkflowInstance
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.config_registry import ConfigRegistry
from app.services.workflow_service import WorkflowService


class RuleViolationError(Exception):
    pass


class PurchaseRequestService:
    def __init__(self, db: Session, registry: ConfigRegistry) -> None:
        self.db = db
        self.registry = registry
        self.workflow = WorkflowService(db, registry)
        self.audit = AuditService(db)
        self.approvals = ApprovalService(db)

    def _next_code(self) -> str:
        last = self.db.query(PurchaseRequest).order_by(PurchaseRequest.id.desc()).first()
        next_no = 1 if not last else last.id + 1
        return f"PR-{next_no:06d}"

    def create(self, payload) -> PurchaseRequest:
        pr = PurchaseRequest(
            code=self._next_code(),
            requester=payload.requester,
            department=payload.department,
            need_date=payload.need_date.isoformat() if payload.need_date else None,
            reason=payload.reason,
            cost_center_code=payload.cost_center_code,
            budget_status=payload.budget_status,
            priority=payload.priority,
            total_estimated_amount=Decimal(str(payload.total_estimated_amount)),
            currency=payload.currency,
            status="draft",
            created_by=payload.created_by or payload.requester,
            modified_by=payload.created_by or payload.requester,
        )
        self.db.add(pr)
        self.db.flush()

        for line in payload.lines:
            self.db.add(
                PurchaseRequestLine(
                    purchase_request_id=pr.id,
                    line_no=line.line_no,
                    description=line.description,
                    material_code=line.material_code,
                    qty=Decimal(str(line.qty)),
                    uom=line.uom,
                    estimated_unit_price=Decimal(str(line.estimated_unit_price)) if line.estimated_unit_price is not None else None,
                    cost_center_code=line.cost_center_code,
                    status="open",
                    created_by=payload.created_by or payload.requester,
                    modified_by=payload.created_by or payload.requester,
                )
            )

        instance = self.workflow.create_instance(
            process_name="procurement",
            object_type="PurchaseRequest",
            object_id=pr.id,
            current_owner=pr.requester,
            current_role="Requester",
            financial_impact=float(payload.total_estimated_amount),
        )
        pr.workflow_instance_id = instance.id
        self.audit.log(
            user_name=payload.created_by or payload.requester,
            entity_name="purchase_requests",
            entity_id=str(pr.id),
            action="create",
            new_value=pr.code,
        )
        self.db.commit()
        self.db.refresh(pr)
        return pr

    def get(self, pr_id: int) -> PurchaseRequest | None:
        return self.db.query(PurchaseRequest).filter(PurchaseRequest.id == pr_id).first()

    def list(self) -> list[PurchaseRequest]:
        return self.db.query(PurchaseRequest).order_by(PurchaseRequest.id.desc()).all()

    def get_lines(self, pr_id: int) -> list[PurchaseRequestLine]:
        return self.db.query(PurchaseRequestLine).filter(PurchaseRequestLine.purchase_request_id == pr_id).order_by(PurchaseRequestLine.line_no).all()

    def get_workflow_instance(self, workflow_instance_id: int | None) -> WorkflowInstance | None:
        if not workflow_instance_id:
            return None
        return self.db.query(WorkflowInstance).filter(WorkflowInstance.id == workflow_instance_id).first()

    def submit(self, pr_id: int, actor: str, actor_role: str, exception_approved: bool = False) -> PurchaseRequest:
        pr = self.get(pr_id)
        if not pr:
            raise RuleViolationError("purchase request not found")
        if pr.status != "draft":
            raise RuleViolationError("only draft purchase request can be submitted")

        lines = self.get_lines(pr.id)
        if not lines:
            raise RuleViolationError("PR-001: at least one line is required")
        if not pr.reason or not pr.reason.strip():
            raise RuleViolationError("PR-001: reason is mandatory")
        if not pr.cost_center_code:
            raise RuleViolationError("PR-001: cost center is mandatory")
        if any(not line.cost_center_code for line in lines):
            raise RuleViolationError("PR-001: all lines must have cost center")
        if pr.budget_status not in {"within_budget", "approved_exception"} and not exception_approved:
            raise RuleViolationError("PR-002: budget exception approval is required")

        instance = self.get_workflow_instance(pr.workflow_instance_id)
        if not instance:
            raise RuleViolationError("workflow instance not found")

        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="submit",
            actor=actor,
            actor_role=actor_role,
        )
        pr.status = "submitted"
        pr.modified_by = actor
        self.audit.log(
            user_name=actor,
            entity_name="purchase_requests",
            entity_id=str(pr.id),
            action="submit",
            old_value="draft",
            new_value="submitted",
            reason="server-side workflow transition",
        )
        self.db.commit()
        self.db.refresh(pr)
        return pr

    def route_review(self, pr_id: int, actor: str, actor_role: str, note: str | None = None) -> PurchaseRequest:
        pr = self.get(pr_id)
        if not pr:
            raise RuleViolationError("purchase request not found")
        if pr.status != "submitted":
            raise RuleViolationError("only submitted purchase request can be moved to review")
        instance = self.get_workflow_instance(pr.workflow_instance_id)
        if not instance:
            raise RuleViolationError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="route_review",
            actor=actor,
            actor_role=actor_role,
        )
        pr.status = "under_review"
        pr.modified_by = actor
        self.audit.log(
            user_name=actor,
            entity_name="purchase_requests",
            entity_id=str(pr.id),
            action="route_review",
            old_value="submitted",
            new_value="under_review",
            reason=note,
        )
        self.db.commit()
        self.db.refresh(pr)
        return pr

    def approve(self, pr_id: int, actor: str, actor_role: str, note: str | None = None) -> PurchaseRequest:
        pr = self.get(pr_id)
        if not pr:
            raise RuleViolationError("purchase request not found")
        if pr.status != "under_review":
            raise RuleViolationError("only under review purchase request can be approved")
        if pr.requester == actor:
            raise RuleViolationError("SOD-001: requester cannot be final approver for the same purchase request")
        instance = self.get_workflow_instance(pr.workflow_instance_id)
        if not instance:
            raise RuleViolationError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="approve",
            actor=actor,
            actor_role=actor_role,
        )
        pr.status = "approved"
        pr.modified_by = actor
        self.approvals.record(
            object_type="PurchaseRequest",
            object_id=pr.id,
            approval_stage="pr_final",
            approver_name=actor,
            approver_role=actor_role,
            decision="approved",
            decision_note=note,
        )
        self.audit.log(
            user_name=actor,
            entity_name="purchase_requests",
            entity_id=str(pr.id),
            action="approve",
            old_value="under_review",
            new_value="approved",
            reason=note,
        )
        self.db.commit()
        self.db.refresh(pr)
        return pr
