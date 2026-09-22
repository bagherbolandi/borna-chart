from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.db import SessionLocal
from app.models.master import AuditLog
from app.models.security import AuthToken


def auth_headers(client: TestClient, username: str, password: str | None = None) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password or username})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_security_dashboard_shows_locked_users_and_recent_security_events(client: TestClient) -> None:
    for _ in range(settings.max_failed_login_attempts):
        resp = client.post("/api/v1/auth/login", json={"username": "buyer.2", "password": "wrong"})
        assert resp.status_code == 401, resp.text

    locked_resp = client.post("/api/v1/auth/login", json={"username": "buyer.2", "password": "buyer.2"})
    assert locked_resp.status_code == 423, locked_resp.text

    logout_headers = auth_headers(client, "sales.1")
    logout_resp = client.post("/api/v1/auth/logout", headers=logout_headers)
    assert logout_resp.status_code == 200, logout_resp.text

    invalid_token_use = client.get("/api/v1/auth/me", headers=logout_headers)
    assert invalid_token_use.status_code == 401, invalid_token_use.text

    dashboard_resp = client.get("/api/v1/dashboard/security", headers=auth_headers(client, "security.1"))
    assert dashboard_resp.status_code == 200, dashboard_resp.text
    body = dashboard_resp.json()
    assert "buyer.2" in body["locked_usernames"]
    assert body["login_failures_24h"] >= settings.max_failed_login_attempts
    assert body["invalid_token_events_24h"] >= 1
    assert body["revoked_tokens"] >= 1
    assert body["suspicious_events_24h"] >= body["login_failures_24h"]
    assert any(event["action"] in {"login_failed", "account_locked", "revoked_token"} for event in body["recent_events"])


def test_security_token_cleanup_removes_expired_and_revoked_tokens(client: TestClient) -> None:
    revoked_headers = auth_headers(client, "sales.mgr")
    revoke_resp = client.post("/api/v1/auth/logout", headers=revoked_headers)
    assert revoke_resp.status_code == 200, revoke_resp.text

    expired_headers = auth_headers(client, "manager.1")
    expired_token = expired_headers["Authorization"].split(" ", 1)[1]

    db = SessionLocal()
    try:
        token_row = db.query(AuthToken).filter(AuthToken.token == expired_token).first()
        assert token_row is not None
        token_row.expires_at = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        db.commit()
    finally:
        db.close()

    cleanup_headers = auth_headers(client, "security.1")
    cleanup_resp = client.post("/api/v1/security/tokens/cleanup", headers=cleanup_headers)
    assert cleanup_resp.status_code == 200, cleanup_resp.text
    payload = cleanup_resp.json()
    assert payload["removed_expired_tokens"] >= 1
    assert payload["removed_revoked_tokens"] >= 1
    assert payload["remaining_active_tokens"] >= 1

    db = SessionLocal()
    try:
        actions = [
            row.action
            for row in db.query(AuditLog)
            .filter(AuditLog.entity_name == "auth", AuditLog.entity_id == "security.1")
            .order_by(AuditLog.id.asc())
            .all()
        ]
        assert "token_cleanup" in actions
    finally:
        db.close()
