from pydantic import BaseModel


class SecurityRecentEvent(BaseModel):
    event_time: str
    username: str | None = None
    action: str
    reason: str | None = None


class SecurityDashboardSummary(BaseModel):
    locked_usernames: list[str]
    active_tokens: int
    revoked_tokens: int
    expired_tokens: int
    open_incidents: int
    critical_open_incidents: int
    login_successes_24h: int
    login_failures_24h: int
    rate_limit_blocks_24h: int
    invalid_token_events_24h: int
    suspicious_events_24h: int
    recent_events: list[SecurityRecentEvent]


class TokenCleanupResult(BaseModel):
    removed_expired_tokens: int
    removed_revoked_tokens: int
    remaining_active_tokens: int
    detail: str
