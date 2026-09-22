from fastapi.testclient import TestClient


def login(client: TestClient, username: str, password: str | None = None):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password or username})


def auth_headers(client: TestClient, username: str, password: str | None = None) -> dict[str, str]:
    resp = login(client, username, password)
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_password_policy_blocks_weak_password_on_user_creation(client: TestClient) -> None:
    admin_headers = auth_headers(client, "master.admin")
    weak_resp = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "weak.user",
            "password": "weak",
            "full_name": "Weak User",
            "department_code": "ops",
            "role_code": "Requester",
            "status": "active",
        },
    )
    assert weak_resp.status_code == 409, weak_resp.text
    assert "password policy violation" in weak_resp.json()["detail"]

    strong_resp = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "strong.user",
            "password": "Strong#1234",
            "full_name": "Strong User",
            "department_code": "ops",
            "role_code": "Requester",
            "status": "active",
        },
    )
    assert strong_resp.status_code == 201, strong_resp.text
    assert strong_resp.json()["username"] == "strong.user"


def test_forced_password_reset_blocks_operational_use_until_password_change(client: TestClient) -> None:
    admin_headers = auth_headers(client, "master.admin")
    create_resp = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "reset.user",
            "password": "Start#1234",
            "full_name": "Reset User",
            "department_code": "ops",
            "role_code": "Requester",
            "status": "active",
        },
    )
    assert create_resp.status_code == 201, create_resp.text

    force_resp = client.post("/api/v1/users/reset.user/force-password-reset", headers=auth_headers(client, "security.1"))
    assert force_resp.status_code == 200, force_resp.text

    login_resp = login(client, "reset.user", "Start#1234")
    assert login_resp.status_code == 200, login_resp.text
    assert login_resp.json()["password_reset_required"] is True
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    blocked_resp = client.get("/api/v1/alerts", headers=headers)
    assert blocked_resp.status_code == 403, blocked_resp.text
    assert "password change required" in blocked_resp.json()["detail"]

    change_resp = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "Start#1234", "new_password": "Changed#5678"},
    )
    assert change_resp.status_code == 200, change_resp.text

    allowed_resp = client.get("/api/v1/alerts", headers=headers)
    assert allowed_resp.status_code == 200, allowed_resp.text


def test_session_inventory_and_revoke_workflow(client: TestClient) -> None:
    sales_login_1 = login(client, "sales.1")
    assert sales_login_1.status_code == 200, sales_login_1.text
    sales_token_1 = sales_login_1.json()["access_token"]

    sales_login_2 = login(client, "sales.1")
    assert sales_login_2.status_code == 200, sales_login_2.text
    sales_token_2 = sales_login_2.json()["access_token"]
    sales_headers_2 = {"Authorization": f"Bearer {sales_token_2}"}

    my_sessions_resp = client.get("/api/v1/security/my-sessions", headers=sales_headers_2)
    assert my_sessions_resp.status_code == 200, my_sessions_resp.text
    my_sessions = my_sessions_resp.json()
    assert my_sessions["total_count"] >= 2
    assert any(item["is_current"] is True for item in my_sessions["items"])

    revoke_id = next(item["id"] for item in my_sessions["items"] if item["is_current"] is False)

    security_headers = auth_headers(client, "security.1")
    inv_resp = client.get("/api/v1/security/sessions", headers=security_headers, params={"username": "sales.1"})
    assert inv_resp.status_code == 200, inv_resp.text
    items = inv_resp.json()["items"]
    assert len(items) >= 2

    revoke_resp = client.post(f"/api/v1/security/sessions/{revoke_id}/revoke", headers=security_headers)
    assert revoke_resp.status_code == 200, revoke_resp.text
    assert revoke_resp.json()["detail"] == "session revoked"

    revoked_use = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {sales_token_1}"})
    assert revoked_use.status_code == 401, revoked_use.text
    assert revoked_use.json()["detail"] == "token revoked"

    still_active = client.get("/api/v1/auth/me", headers=sales_headers_2)
    assert still_active.status_code == 200, still_active.text
