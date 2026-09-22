from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import AuditMixin


class WorkflowDefinition(AuditMixin, Base):
    __tablename__ = "workflow_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    process_name: Mapped[str] = mapped_column(String(100), nullable=False)
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    version_no: Mapped[int] = mapped_column(default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    states: Mapped[list["WorkflowState"]] = relationship(back_populates="workflow_definition")


class WorkflowState(AuditMixin, Base):
    __tablename__ = "workflow_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_definition_id: Mapped[int] = mapped_column(ForeignKey("workflow_definitions.id"), nullable=False)
    state_code: Mapped[str] = mapped_column(String(50), nullable=False)
    state_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    workflow_definition: Mapped[WorkflowDefinition] = relationship(back_populates="states")


class WorkflowTransition(AuditMixin, Base):
    __tablename__ = "workflow_transitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_definition_id: Mapped[int] = mapped_column(ForeignKey("workflow_definitions.id"), nullable=False)
    from_state_code: Mapped[str] = mapped_column(String(50), nullable=False)
    to_state_code: Mapped[str] = mapped_column(String(50), nullable=False)
    action_code: Mapped[str] = mapped_column(String(50), nullable=False)
    allowed_roles_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    rule_codes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class WorkflowInstance(AuditMixin, Base):
    __tablename__ = "workflow_instances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    object_id: Mapped[int] = mapped_column(nullable=False)
    process_name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_state: Mapped[str] = mapped_column(String(50), nullable=False)
    current_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    due_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    escalation_level: Mapped[int] = mapped_column(default=0, nullable=False)
    exception_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    financial_impact: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)


class Approval(AuditMixin, Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    object_id: Mapped[int] = mapped_column(nullable=False)
    approval_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    approver_name: Mapped[str] = mapped_column(String(100), nullable=False)
    approver_role: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[str] = mapped_column(String(40), nullable=False)


class Alert(AuditMixin, Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_code: Mapped[str] = mapped_column(String(50), nullable=False)
    related_object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    related_object_id: Mapped[int] = mapped_column(nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation_level: Mapped[int] = mapped_column(default=0, nullable=False)
    financial_impact: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
