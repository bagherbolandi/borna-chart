from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.db import SessionLocal
from app.models.master import AuditLog, User


def test_logout_revokes_active_token(client: TestClient) -> None:
    login_resp = client.post("/api/v1/auth/login", json={"username": "sales.1", "password": "sales.1"})
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200, me_resp.text

    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200, logout_resp.text
    assert logout_resp.json()["detail"] == "logged out"

    revoked_resp = client.get("/api/v1/auth/me", headers=headers)
    assert revoked_resp.status_code == 401, revoked_resp.text
    assert revoked_resp.json()["detail"] == "token revoked"


def test_failed_logins_lock_account_and_create_audit_events(client: TestClient) -> None:
    for _ in range(settings.max_failed_login_attempts):
        resp = client.post("/api/v1/auth/login", json={"username": "buyer.1", "password": "wrong-password"})
        assert resp.status_code == 401, resp.text

    locked_resp = client.post("/api/v1/auth/login", json={"username": "buyer.1", "password": "buyer.1"})
    assert locked_resp.status_code == 423, locked_resp.text
    assert "account temporarily locked" in locked_resp.json()["detail"]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "buyer.1").first()
        assert user is not None
        assert user.failed_login_attempts >= settings.max_failed_login_attempts
        assert user.locked_until is not None

        actions = [
            row.action
            for row in db.query(AuditLog)
            .filter(AuditLog.entity_name == "auth", AuditLog.entity_id == "buyer.1")
            .order_by(AuditLog.id.asc())
            .all()
        ]
        assert "login_failed" in actions
        assert "account_locked" in actions
        assert "login_blocked" in actions
    finally:
        db.close()


def test_login_rate_limit_blocks_repeated_attempts(client: TestClient) -> None:
    for _ in range(settings.login_rate_limit_attempts):
        resp = client.post("/api/v1/auth/login", json={"username": "ghost.user", "password": "bad"})
        assert resp.status_code == 401, resp.text

    blocked_resp = client.post("/api/v1/auth/login", json={"username": "ghost.user", "password": "bad"})
    assert blocked_resp.status_code == 429, blocked_resp.text
    assert blocked_resp.json()["detail"] == "too many login attempts, retry later"
    assert int(blocked_resp.headers["Retry-After"]) >= 1

    db = SessionLocal()
    try:
        actions = [
            row.action
            for row in db.query(AuditLog)
            .filter(AuditLog.entity_name == "auth", AuditLog.entity_id == "ghost.user")
            .order_by(AuditLog.id.asc())
            .all()
        ]
        assert "rate_limit_block" in actions
    finally:
        db.close()
