from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.audit import AuditSearchResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/events", response_model=AuditSearchResponse)
def search_audit_events(
    entity_name: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    user_name: str | None = None,
    q: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> AuditSearchResponse:
    return AuditService(db).search(
        entity_name=entity_name,
        entity_id=entity_id,
        action=action,
        user_name=user_name,
        q=q,
        start_time=start_time.isoformat() if start_time else None,
        end_time=end_time.isoformat() if end_time else None,
        limit=limit,
    )


@router.get("/entities/{entity_name}/{entity_id}", response_model=AuditSearchResponse)
def audit_for_entity(
    entity_name: str,
    entity_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> AuditSearchResponse:
    return AuditService(db).search(entity_name=entity_name, entity_id=entity_id, limit=limit)
