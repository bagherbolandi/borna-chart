from pydantic import BaseModel

from app.schemas.common import ORMModel


class SessionRead(ORMModel):
    id: int
    username: str
    created_at: str
    expires_at: str
    revoked_at: str | None = None
    is_active: bool
    is_current: bool = False


class SessionInventoryResponse(BaseModel):
    total_count: int
    items: list[SessionRead]
