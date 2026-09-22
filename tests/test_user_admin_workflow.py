from fastapi.testclient import TestClient


def login(client: TestClient, username: str, password: str | None = None):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password or username})


def auth_headers(client: TestClient, username: str, password: str | None = None) -> dict[str, str]:
    resp = login(client, username, password)
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_admin_can_update_user_unlock_and_revoke_sessions(client: TestClient) -> None:
    admin_headers = auth_headers(client, "master.admin")

    create_resp = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "ops.user",
            "password": "Strong#1234",
            "full_name": "Operations User",
            "department_code": "ops",
            "role_code": "Requester",
            "status": "active",
        },
    )
    assert create_resp.status_code == 201, create_resp.text

    update_resp = client.patch(
        "/api/v1/users/ops.user",
        headers=admin_headers,
        json={
            "full_name": "Operations Planner",
            "department_code": "planning",
            "role_code": "Planning Officer",
            "status": "inactive",
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    data = update_resp.json()
    assert data["full_name"] == "Operations Planner"
    assert data["department_code"] == "planning"
    assert data["role_code"] == "Planning Officer"
    assert data["status"] == "inactive"

    inactive_login = login(client, "ops.user", "Strong#1234")
    assert inactive_login.status_code == 401, inactive_login.text

    reactivate_resp = client.patch(
        "/api/v1/users/ops.user",
        headers=admin_headers,
        json={"status": "active"},
    )
    assert reactivate_resp.status_code == 200, reactivate_resp.text
    assert reactivate_resp.json()["status"] == "active"

    for _ in range(5):
        bad = login(client, "ops.user", "wrong-password")
        if bad.status_code == 423:
            break
        assert bad.status_code == 401, bad.text

    locked = login(client, "ops.user", "Strong#1234")
    assert locked.status_code == 423, locked.text

    unlock_resp = client.post("/api/v1/users/ops.user/unlock", headers=auth_headers(client, "security.1"))
    assert unlock_resp.status_code == 200, unlock_resp.text
    assert unlock_resp.json()["detail"] == "user unlocked"

    first_login = login(client, "ops.user", "Strong#1234")
    assert first_login.status_code == 200, first_login.text
    second_login = login(client, "ops.user", "Strong#1234")
    assert second_login.status_code == 200, second_login.text

    revoke_resp = client.post("/api/v1/users/ops.user/revoke-sessions", headers=admin_headers)
    assert revoke_resp.status_code == 200, revoke_resp.text
    assert revoke_resp.json()["detail"] == "all sessions revoked"

    token_1 = first_login.json()["access_token"]
    token_2 = second_login.json()["access_token"]
    me_1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_1}"})
    me_2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_2}"})
    assert me_1.status_code == 401, me_1.text
    assert me_2.status_code == 401, me_2.text
