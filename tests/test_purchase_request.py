from fastapi.testclient import TestClient


def auth_headers(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": username})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_submit_purchase_request_success(client: TestClient) -> None:
    requester_headers = auth_headers(client, "ali")
    create_resp = client.post(
        "/api/v1/purchase-requests",
        headers=requester_headers,
        json={
            "requester": "ali",
            "department": "procurement",
            "reason": "raw material needed",
            "cost_center_code": "CC-100",
            "budget_status": "within_budget",
            "priority": "high",
            "total_estimated_amount": 1000,
            "currency": "IRR",
            "lines": [
                {
                    "line_no": 1,
                    "description": "steel sheet",
                    "qty": 10,
                    "uom": "kg",
                    "estimated_unit_price": 100,
                    "cost_center_code": "CC-100",
                }
            ],
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    pr_id = create_resp.json()["id"]

    submit_resp = client.post(
        f"/api/v1/purchase-requests/{pr_id}/submit",
        headers=requester_headers,
        json={"actor": "ali", "actor_role": "Requester", "exception_approved": False},
    )
    assert submit_resp.status_code == 200, submit_resp.text
    assert submit_resp.json()["status"] == "submitted"


def test_submit_purchase_request_blocked_without_cost_center(client: TestClient) -> None:
    requester_headers = auth_headers(client, "reza")
    create_resp = client.post(
        "/api/v1/purchase-requests",
        headers=requester_headers,
        json={
            "requester": "reza",
            "department": "maintenance",
            "reason": "urgent spare part",
            "budget_status": "within_budget",
            "priority": "high",
            "total_estimated_amount": 500,
            "currency": "IRR",
            "lines": [
                {
                    "line_no": 1,
                    "description": "bearing",
                    "qty": 2,
                    "uom": "pcs",
                    "estimated_unit_price": 250,
                    "cost_center_code": "CC-200",
                }
            ],
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    pr_id = create_resp.json()["id"]

    submit_resp = client.post(
        f"/api/v1/purchase-requests/{pr_id}/submit",
        headers=requester_headers,
        json={"actor": "reza", "actor_role": "Requester", "exception_approved": False},
    )
    assert submit_resp.status_code == 409, submit_resp.text
    assert "PR-001" in submit_resp.json()["detail"]
