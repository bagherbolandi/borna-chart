from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowState, WorkflowTransition
from app.services.alert_service import AlertService
from app.services.config_registry import ConfigRegistry
from app.services.sla_service import SLAService


class WorkflowError(Exception):
    pass


class WorkflowService:
    def __init__(self, db: Session, registry: ConfigRegistry) -> None:
        self.db = db
        self.registry = registry

    def seed_definitions(self) -> None:
        workflows = self.registry.get_workflows()
        for code, data in workflows.items():
            exists = self.db.query(WorkflowDefinition).filter(WorkflowDefinition.code == code).first()
            if exists:
                continue
            wf = WorkflowDefinition(
                code=code,
                process_name=data["process"],
                object_type=data["object_type"],
                version_no=1,
                is_active=True,
                created_by="system",
                modified_by="system",
            )
            self.db.add(wf)
            self.db.flush()
            for state in data.get("states", []):
                self.db.add(
                    WorkflowState(
                        workflow_definition_id=wf.id,
                        state_code=state["code"],
                        state_name=state["name"],
                        is_initial=bool(state.get("initial", False)),
                        is_final=bool(state.get("final", False)),
                        created_by="system",
                        modified_by="system",
                    )
                )
            for transition in data.get("transitions", []):
                self.db.add(
                    WorkflowTransition(
                        workflow_definition_id=wf.id,
                        from_state_code=transition["from"],
                        to_state_code=transition["to"],
                        action_code=transition["action"],
                        allowed_roles_json=json.dumps(transition.get("roles", []), ensure_ascii=False),
                        rule_codes_json=json.dumps(transition.get("rules", []), ensure_ascii=False),
                        created_by="system",
                        modified_by="system",
                    )
                )
        self.db.commit()

    def get_initial_state(self, process_name: str) -> str:
        data = self.registry.get_workflow(process_name)
        if not data:
            raise WorkflowError(f"workflow not found: {process_name}")
        for state in data.get("states", []):
            if state.get("initial"):
                return state["code"]
        raise WorkflowError(f"initial state not found for: {process_name}")

    def create_instance(
        self,
        *,
        process_name: str,
        object_type: str,
        object_id: int,
        current_owner: str | None,
        current_role: str | None,
        financial_impact: float = 0,
        initial_state: str | None = None,
    ) -> WorkflowInstance:
        state = initial_state or self.get_initial_state(process_name)
        instance = WorkflowInstance(
            process_name=process_name,
            object_type=object_type,
            object_id=object_id,
            current_state=state,
            current_owner=current_owner,
            current_role=current_role,
            due_at=None,
            financial_impact=financial_impact,
            created_by=current_owner,
            modified_by=current_owner,
        )
        self.db.add(instance)
        self.db.flush()
        SLAService(self.db, self.registry).assign_due_at(instance)
        self.db.flush()
        return instance

    def allowed_transition(self, process_name: str, from_state: str, action: str, actor_role: str) -> dict:
        data = self.registry.get_workflow(process_name)
        if not data:
            raise WorkflowError(f"workflow not found: {process_name}")
        for transition in data.get("transitions", []):
            roles = transition.get("roles", [])
            if transition["from"] == from_state and transition["action"] == action:
                if "System" in roles or actor_role in roles or "Any Authorized User" in roles:
                    return transition
                raise WorkflowError(f"role '{actor_role}' is not allowed for action '{action}' from state '{from_state}'")
        raise WorkflowError(f"transition not found for state '{from_state}' and action '{action}'")

    def is_final_state(self, process_name: str, state_code: str) -> bool:
        data = self.registry.get_workflow(process_name)
        if not data:
            return False
        for state in data.get("states", []):
            if state.get("code") == state_code:
                return bool(state.get("final", False))
        return False

    def apply_transition(
        self,
        *,
        instance: WorkflowInstance,
        process_name: str,
        action: str,
        actor: str,
        actor_role: str,
    ) -> WorkflowInstance:
        transition = self.allowed_transition(process_name, instance.current_state, action, actor_role)
        instance.current_state = transition["to"]
        instance.current_owner = actor
        instance.current_role = actor_role
        instance.modified_by = actor
        instance.modified_at = datetime.now(UTC)
        instance.escalation_level = 0
        if self.is_final_state(process_name, instance.current_state):
            instance.status = "closed"
            instance.due_at = None
        else:
            instance.status = "open"
            SLAService(self.db, self.registry).assign_due_at(instance)
        AlertService(self.db).resolve_for_object(
            related_object_type=instance.object_type,
            related_object_id=instance.object_id,
        )
        self.db.flush()
        return instance
