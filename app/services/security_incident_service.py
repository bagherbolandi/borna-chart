from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.master import AuditLog
from app.models.security import SecurityIncident
from app.models.workflow import WorkflowInstance
from app.services.audit_service import AuditService
from app.services.config_registry import ConfigRegistry
from app.services.workflow_service import WorkflowError, WorkflowService


class SecurityIncidentError(Exception):
    pass


class SecurityIncidentService:
    def __init__(self, db: Session, registry: ConfigRegistry) -> None:
        self.db = db
        self.registry = registry
        self.workflow = WorkflowService(db, registry)
        self.audit = AuditService(db)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _next_code(self) -> str:
        last = self.db.query(SecurityIncident).order_by(SecurityIncident.id.desc()).first()
        next_no = 1 if not last else last.id + 1
        return f"SEC-{next_no:06d}"

    def _get_incident(self, incident_id: int) -> SecurityIncident | None:
        return self.db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()

    def _get_workflow(self, workflow_instance_id: int | None) -> WorkflowInstance | None:
        if not workflow_instance_id:
            return None
        return self.db.query(WorkflowInstance).filter(WorkflowInstance.id == workflow_instance_id).first()

    def _validate_audit_log_ids(self, audit_log_ids: list[int]) -> None:
        if not audit_log_ids:
            return
        found_ids = {
            row.id
            for row in self.db.query(AuditLog).filter(AuditLog.id.in_(audit_log_ids)).all()
        }
        missing = [row_id for row_id in audit_log_ids if row_id not in found_ids]
        if missing:
            raise SecurityIncidentError(f"audit log ids not found: {missing}")

    def list_incidents(self) -> list[SecurityIncident]:
        return self.db.query(SecurityIncident).order_by(SecurityIncident.id.desc()).all()

    def get_incident(self, incident_id: int) -> SecurityIncident | None:
        return self._get_incident(incident_id)

    def create_incident(self, payload) -> SecurityIncident:
        self._validate_audit_log_ids(payload.audit_log_ids)
        assigned_to = payload.assigned_to or payload.actor
        incident = SecurityIncident(
            code=self._next_code(),
            title=payload.title,
            incident_type=payload.incident_type,
            severity=payload.severity.lower(),
            related_username=payload.related_username,
            source_entity_name=payload.source_entity_name,
            source_entity_id=payload.source_entity_id,
            evidence_refs_json=json.dumps(payload.audit_log_ids, ensure_ascii=False) if payload.audit_log_ids else None,
            summary=payload.summary,
            assigned_to=assigned_to,
            containment_action=None,
            resolution_note=None,
            detected_at=self._now(),
            closed_at=None,
            status="open",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(incident)
        self.db.flush()
        instance = self.workflow.create_instance(
            process_name="security_incident",
            object_type="SecurityIncident",
            object_id=incident.id,
            current_owner=assigned_to,
            current_role=payload.actor_role,
            initial_state="open",
        )
        incident.workflow_instance_id = instance.id
        self.audit.log(
            user_name=payload.actor,
            entity_name="security_incidents",
            entity_id=str(incident.id),
            action="create",
            new_value=incident.code,
            reason=payload.summary,
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def _apply(self, incident: SecurityIncident, *, action: str, actor: str, actor_role: str) -> WorkflowInstance:
        instance = self._get_workflow(incident.workflow_instance_id)
        if not instance:
            raise SecurityIncidentError("workflow instance not found")
        try:
            return self.workflow.apply_transition(
                instance=instance,
                process_name="security_incident",
                action=action,
                actor=actor,
                actor_role=actor_role,
            )
        except WorkflowError as exc:
            raise SecurityIncidentError(str(exc)) from exc

    def triage_incident(self, incident_id: int, payload) -> SecurityIncident:
        incident = self._get_incident(incident_id)
        if not incident:
            raise SecurityIncidentError("security incident not found")
        self._apply(incident, action="triage_incident", actor=payload.actor, actor_role=payload.actor_role)
        incident.status = "under_review"
        incident.assigned_to = payload.assigned_to or incident.assigned_to or payload.actor
        incident.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="security_incidents",
            entity_id=str(incident.id),
            action="triage",
            old_value="open",
            new_value="under_review",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def contain_incident(self, incident_id: int, payload) -> SecurityIncident:
        incident = self._get_incident(incident_id)
        if not incident:
            raise SecurityIncidentError("security incident not found")
        if not payload.containment_action:
            raise SecurityIncidentError("containment action is required")
        self._apply(incident, action="contain_incident", actor=payload.actor, actor_role=payload.actor_role)
        incident.status = "contained"
        incident.containment_action = payload.containment_action
        incident.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="security_incidents",
            entity_id=str(incident.id),
            action="contain",
            old_value="under_review",
            new_value="contained",
            reason=payload.note or payload.containment_action,
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def resolve_incident(self, incident_id: int, payload) -> SecurityIncident:
        incident = self._get_incident(incident_id)
        if not incident:
            raise SecurityIncidentError("security incident not found")
        if not payload.resolution_note:
            raise SecurityIncidentError("resolution note is required")
        self._apply(incident, action="resolve_incident", actor=payload.actor, actor_role=payload.actor_role)
        incident.status = "resolved"
        incident.resolution_note = payload.resolution_note
        incident.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="security_incidents",
            entity_id=str(incident.id),
            action="resolve",
            old_value="contained",
            new_value="resolved",
            reason=payload.note or payload.resolution_note,
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def close_incident(self, incident_id: int, payload) -> SecurityIncident:
        incident = self._get_incident(incident_id)
        if not incident:
            raise SecurityIncidentError("security incident not found")
        self._apply(incident, action="close_incident", actor=payload.actor, actor_role=payload.actor_role)
        incident.status = "closed"
        incident.closed_at = self._now()
        incident.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="security_incidents",
            entity_id=str(incident.id),
            action="close",
            old_value="resolved",
            new_value="closed",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident
