from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.master import AuditLog
from app.schemas.audit import AuditLogRead, AuditSearchResponse


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        *,
        user_name: str | None,
        entity_name: str,
        entity_id: str,
        action: str,
        field_name: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        reason: str | None = None,
        authorized_by: str | None = None,
    ) -> None:
        row = AuditLog(
            event_time=datetime.now(UTC).isoformat(),
            user_name=user_name,
            entity_name=entity_name,
            entity_id=entity_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            authorized_by=authorized_by,
        )
        self.db.add(row)
        self.db.flush()

    def search(
        self,
        *,
        entity_name: str | None = None,
        entity_id: str | None = None,
        action: str | None = None,
        user_name: str | None = None,
        q: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 100,
    ) -> AuditSearchResponse:
        query = self.db.query(AuditLog)
        if entity_name:
            query = query.filter(AuditLog.entity_name == entity_name)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_name:
            query = query.filter(AuditLog.user_name == user_name)
        rows = query.order_by(AuditLog.id.desc()).all()

        def matches(row: AuditLog) -> bool:
            if start_time and row.event_time < start_time:
                return False
            if end_time and row.event_time > end_time:
                return False
            if q:
                haystack = " | ".join(
                    str(value or "")
                    for value in [
                        row.entity_name,
                        row.entity_id,
                        row.action,
                        row.user_name,
                        row.field_name,
                        row.old_value,
                        row.new_value,
                        row.reason,
                        row.authorized_by,
                    ]
                ).lower()
                if q.lower() not in haystack:
                    return False
            return True

        filtered = [row for row in rows if matches(row)]
        items = [AuditLogRead.model_validate(row) for row in filtered[:limit]]
        return AuditSearchResponse(total_count=len(filtered), items=items)
