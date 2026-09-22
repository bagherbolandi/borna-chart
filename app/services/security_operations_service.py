from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.master import AuditLog, User
from app.models.security import AuthToken, SecurityIncident
from app.schemas.security_dashboard import SecurityDashboardSummary, SecurityRecentEvent, TokenCleanupResult
from app.services.audit_service import AuditService


@dataclass
class _TokenCounters:
    active: int = 0
    revoked: int = 0
    expired: int = 0


class SecurityOperationsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value)

    def _token_counters(self) -> _TokenCounters:
        now = self._now()
        counters = _TokenCounters()
        for token in self.db.query(AuthToken).all():
            expires_at = self._parse_dt(token.expires_at)
            if token.revoked_at:
                counters.revoked += 1
            elif expires_at and expires_at <= now:
                counters.expired += 1
            else:
                counters.active += 1
        return counters

    def _locked_usernames(self) -> list[str]:
        now = self._now()
        locked: list[str] = []
        for user in self.db.query(User).order_by(User.username.asc()).all():
            locked_until = self._parse_dt(user.locked_until)
            if locked_until and locked_until > now:
                locked.append(user.username)
        return locked

    def _auth_events_last_24h(self) -> list[AuditLog]:
        since = self._now() - timedelta(hours=24)
        rows = (
            self.db.query(AuditLog)
            .filter(AuditLog.entity_name == "auth")
            .order_by(AuditLog.id.desc())
            .all()
        )
        return [row for row in rows if self._parse_dt(row.event_time) and self._parse_dt(row.event_time) >= since]

    def dashboard_summary(self) -> SecurityDashboardSummary:
        counters = self._token_counters()
        recent_auth_events = (
            self.db.query(AuditLog)
            .filter(AuditLog.entity_name == "auth")
            .order_by(AuditLog.id.desc())
            .limit(settings.security_recent_event_limit)
            .all()
        )
        last_24h = self._auth_events_last_24h()
        login_successes = sum(1 for row in last_24h if row.action == "login_success")
        login_failures = sum(1 for row in last_24h if row.action == "login_failed")
        rate_limit_blocks = sum(1 for row in last_24h if row.action == "rate_limit_block")
        invalid_token_events = sum(1 for row in last_24h if row.action in {"invalid_token", "expired_token", "revoked_token", "invalid_token_user"})
        suspicious_events = sum(
            1
            for row in last_24h
            if row.action in {"login_failed", "account_locked", "login_blocked", "rate_limit_block", "invalid_token", "expired_token", "revoked_token", "invalid_token_user"}
        )
        open_incidents = (
            self.db.query(SecurityIncident)
            .filter(SecurityIncident.status != "closed")
            .count()
        )
        critical_open_incidents = (
            self.db.query(SecurityIncident)
            .filter(SecurityIncident.status != "closed", SecurityIncident.severity == "critical")
            .count()
        )
        return SecurityDashboardSummary(
            locked_usernames=self._locked_usernames(),
            active_tokens=counters.active,
            revoked_tokens=counters.revoked,
            expired_tokens=counters.expired,
            open_incidents=open_incidents,
            critical_open_incidents=critical_open_incidents,
            login_successes_24h=login_successes,
            login_failures_24h=login_failures,
            rate_limit_blocks_24h=rate_limit_blocks,
            invalid_token_events_24h=invalid_token_events,
            suspicious_events_24h=suspicious_events,
            recent_events=[
                SecurityRecentEvent(
                    event_time=row.event_time,
                    username=row.user_name,
                    action=row.action,
                    reason=row.reason,
                )
                for row in recent_auth_events
            ],
        )

    def cleanup_tokens(self, *, actor: str) -> TokenCleanupResult:
        now = self._now()
        removed_expired = 0
        removed_revoked = 0
        rows = self.db.query(AuthToken).all()
        for row in rows:
            expires_at = self._parse_dt(row.expires_at)
            if row.revoked_at:
                self.db.delete(row)
                removed_revoked += 1
            elif expires_at and expires_at <= now:
                self.db.delete(row)
                removed_expired += 1
        self.db.flush()
        counters = self._token_counters()
        self.audit.log(
            user_name=actor,
            entity_name="auth",
            entity_id=actor,
            action="token_cleanup",
            reason=f"removed_expired={removed_expired}; removed_revoked={removed_revoked}",
        )
        self.db.commit()
        return TokenCleanupResult(
            removed_expired_tokens=removed_expired,
            removed_revoked_tokens=removed_revoked,
            remaining_active_tokens=counters.active,
            detail="token cleanup completed",
        )
