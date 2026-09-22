from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SecurityIncidentCreate(BaseModel):
    title: str
    incident_type: str
    severity: str
    related_username: str | None = None
    source_entity_name: str | None = None
    source_entity_id: str | None = None
    audit_log_ids: list[int] = Field(default_factory=list)
    summary: str
    assigned_to: str | None = None
    actor: str
    actor_role: str


class SecurityIncidentAction(BaseModel):
    actor: str
    actor_role: str
    note: str | None = None
    assigned_to: str | None = None
    containment_action: str | None = None
    resolution_note: str | None = None


class SecurityIncidentRead(ORMModel):
    id: int
    code: str
    title: str
    incident_type: str
    severity: str
    related_username: str | None
    source_entity_name: str | None
    source_entity_id: str | None
    evidence_refs_json: str | None
    summary: str
    assigned_to: str | None
    containment_action: str | None
    resolution_note: str | None
    detected_at: str
    closed_at: str | None
    status: str
    workflow_instance_id: int | None
