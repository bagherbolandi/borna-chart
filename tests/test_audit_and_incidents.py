from fastapi.testclient import TestClient


def auth_headers(client: TestClient, username: str, password: str | None = None) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password or username})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_audit_search_filters_and_entity_lookup(client: TestClient) -> None:
    sales_headers = auth_headers(client, "sales.1")
    logout_resp = client.post("/api/v1/auth/logout", headers=sales_headers)
    assert logout_resp.status_code == 200, logout_resp.text

    security_headers = auth_headers(client, "security.1")
    search_resp = client.get(
        "/api/v1/audit/events",
        headers=security_headers,
        params={"entity_name": "auth", "user_name": "sales.1", "action": "logout", "q": "revoked"},
    )
    assert search_resp.status_code == 200, search_resp.text
    payload = search_resp.json()
    assert payload["total_count"] >= 1
    assert any(item["action"] == "logout" and item["entity_name"] == "auth" for item in payload["items"])

    entity_resp = client.get("/api/v1/audit/entities/auth/sales.1", headers=security_headers)
    assert entity_resp.status_code == 200, entity_resp.text
    entity_payload = entity_resp.json()
    assert entity_payload["total_count"] >= 2
    assert any(item["action"] == "login_success" for item in entity_payload["items"])
    assert any(item["action"] == "logout" for item in entity_payload["items"])


def test_security_incident_workflow_and_dashboard_counts(client: TestClient) -> None:
    for _ in range(2):
        resp = client.post("/api/v1/auth/login", json={"username": "buyer.2", "password": "wrong"})
        assert resp.status_code == 401, resp.text

    security_headers = auth_headers(client, "security.1")
    audit_resp = client.get(
        "/api/v1/audit/events",
        headers=security_headers,
        params={"entity_name": "auth", "user_name": "buyer.2", "action": "login_failed"},
    )
    assert audit_resp.status_code == 200, audit_resp.text
    audit_payload = audit_resp.json()
    assert audit_payload["total_count"] >= 2
    audit_ids = [item["id"] for item in audit_payload["items"][:2]]

    create_incident_resp = client.post(
        "/api/v1/security/incidents",
        headers=security_headers,
        json={
            "title": "Repeated failed login attempts for buyer.2",
            "incident_type": "authentication_abuse",
            "severity": "critical",
            "related_username": "buyer.2",
            "source_entity_name": "auth",
            "source_entity_id": "buyer.2",
            "audit_log_ids": audit_ids,
            "summary": "Repeated failed login attempts detected and require review.",
            "assigned_to": "security.1",
            "actor": "security.1",
            "actor_role": "Security Officer",
        },
    )
    assert create_incident_resp.status_code == 201, create_incident_resp.text
    incident_id = create_incident_resp.json()["id"]
    assert create_incident_resp.json()["status"] == "open"

    dashboard_open = client.get("/api/v1/dashboard/security", headers=security_headers)
    assert dashboard_open.status_code == 200, dashboard_open.text
    assert dashboard_open.json()["open_incidents"] >= 1
    assert dashboard_open.json()["critical_open_incidents"] >= 1

    triage_resp = client.post(
        f"/api/v1/security/incidents/{incident_id}/triage",
        headers=security_headers,
        json={
            "actor": "security.1",
            "actor_role": "Security Officer",
            "note": "incident triaged",
            "assigned_to": "security.1",
        },
    )
    assert triage_resp.status_code == 200, triage_resp.text
    assert triage_resp.json()["status"] == "under_review"

    contain_resp = client.post(
        f"/api/v1/security/incidents/{incident_id}/contain",
        headers=security_headers,
        json={
            "actor": "security.1",
            "actor_role": "Security Officer",
            "containment_action": "temporary user lock maintained and IP monitored",
            "note": "containment executed",
        },
    )
    assert contain_resp.status_code == 200, contain_resp.text
    assert contain_resp.json()["status"] == "contained"

    resolve_resp = client.post(
        f"/api/v1/security/incidents/{incident_id}/resolve",
        headers=security_headers,
        json={
            "actor": "security.1",
            "actor_role": "Security Officer",
            "resolution_note": "false-positive risk accepted after review and monitoring applied",
            "note": "resolved after review",
        },
    )
    assert resolve_resp.status_code == 200, resolve_resp.text
    assert resolve_resp.json()["status"] == "resolved"

    close_resp = client.post(
        f"/api/v1/security/incidents/{incident_id}/close",
        headers=security_headers,
        json={
            "actor": "security.1",
            "actor_role": "Security Officer",
            "note": "closed after documentation",
        },
    )
    assert close_resp.status_code == 200, close_resp.text
    assert close_resp.json()["status"] == "closed"

    incident_detail = client.get(f"/api/v1/security/incidents/{incident_id}", headers=security_headers)
    assert incident_detail.status_code == 200, incident_detail.text
    assert incident_detail.json()["closed_at"] is not None

    dashboard_closed = client.get("/api/v1/security/dashboard", headers=security_headers)
    assert dashboard_closed.status_code == 200, dashboard_closed.text
    assert dashboard_closed.json()["open_incidents"] == 0

    incident_audit = client.get(
        f"/api/v1/audit/entities/security_incidents/{incident_id}",
        headers=security_headers,
    )
    assert incident_audit.status_code == 200, incident_audit.text
    actions = [item["action"] for item in incident_audit.json()["items"]]
    assert "create" in actions
    assert "triage" in actions
    assert "contain" in actions
    assert "resolve" in actions
    assert "close" in actions
