from pydantic import BaseModel

from app.schemas.common import ORMModel


class AuditLogRead(ORMModel):
    id: int
    event_time: str
    user_name: str | None
    entity_name: str
    entity_id: str
    action: str
    field_name: str | None
    old_value: str | None
    new_value: str | None
    reason: str | None
    authorized_by: str | None


class AuditSearchResponse(BaseModel):
    total_count: int
    items: list[AuditLogRead]
