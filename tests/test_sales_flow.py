from fastapi.testclient import TestClient


def auth_headers(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": username})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_customer(client: TestClient, code: str, credit_limit: float) -> int:
    resp = client.post(
        "/api/v1/customers",
        headers=auth_headers(client, "master.admin"),
        json={
            "code": code,
            "name": f"Customer {code}",
            "payment_terms": "30D",
            "credit_limit": credit_limit,
            "credit_status": "open",
            "created_by": "master.admin",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def create_product(client: TestClient, code: str, *, min_price: float, cost: float = 100) -> int:
    resp = client.post(
        "/api/v1/products",
        headers=auth_headers(client, "master.admin"),
        json={
            "code": code,
            "name": f"Product {code}",
            "family": "FG",
            "uom": "pcs",
            "standard_cost": cost,
            "approved_min_price": min_price,
            "pricing_method": "Cost Plus",
            "created_by": "master.admin",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def create_price_list(client: TestClient, product_id: int, customer_id: int, *, proposed_price: float, min_price: float) -> int:
    pricing_headers = auth_headers(client, "pricing.1")
    resp = client.post(
        "/api/v1/pricing",
        headers=pricing_headers,
        json={
            "product_id": product_id,
            "customer_id": customer_id,
            "pricing_method": "Cost Plus",
            "cost_basis": 100,
            "target_margin_pct": 20,
            "logistics_cost": 5,
            "financial_cost": 1,
            "risk_cost": 1,
            "proposed_price": proposed_price,
            "approved_min_price": min_price,
            "valid_from": "2026-09-22",
            "actor": "pricing.1",
            "actor_role": "Pricing Analyst",
        },
    )
    assert resp.status_code == 201, resp.text
    price_list_id = resp.json()["id"]

    approve_resp = client.post(
        f"/api/v1/pricing/{price_list_id}/approve",
        headers=pricing_headers,
        json={"actor": "pricing.1", "actor_role": "Pricing Analyst", "note": "approved price"},
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "price_approved"
    return price_list_id


def test_sales_order_success_and_dashboard_counts(client: TestClient) -> None:
    customer_id = create_customer(client, "CUS-100", 10000)
    product_id = create_product(client, "PRD-100", min_price=120)
    price_list_id = create_price_list(client, product_id, customer_id, proposed_price=150, min_price=120)

    sales_headers = auth_headers(client, "sales.1")
    so_resp = client.post(
        "/api/v1/sales-orders",
        headers=sales_headers,
        json={
            "customer_id": customer_id,
            "product_id": product_id,
            "price_list_id": price_list_id,
            "order_date": "2026-09-22",
            "requested_delivery_date": "2026-09-30",
            "qty": 10,
            "unit_price": 150,
            "actor": "sales.1",
            "actor_role": "Sales Officer",
        },
    )
    assert so_resp.status_code == 201, so_resp.text
    so_id = so_resp.json()["id"]
    assert so_resp.json()["status"] == "credit_check"

    confirm_resp = client.post(
        f"/api/v1/sales-orders/{so_id}/confirm",
        headers=auth_headers(client, "sales.mgr"),
        json={"actor": "sales.mgr", "actor_role": "Sales Manager", "note": "confirmed"},
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    assert confirm_resp.json()["status"] == "sales_order_confirmed"
    assert confirm_resp.json()["credit_check_status"] == "passed"

    dashboard_resp = client.get("/api/v1/dashboard/summary", headers=auth_headers(client, "sales.mgr"))
    assert dashboard_resp.status_code == 200, dashboard_resp.text
    assert dashboard_resp.json()["sales_orders_by_status"].get("sales_order_confirmed", 0) >= 1


def test_sales_order_credit_limit_block_creates_alert(client: TestClient) -> None:
    customer_id = create_customer(client, "CUS-200", 500)
    product_id = create_product(client, "PRD-200", min_price=100)
    price_list_id = create_price_list(client, product_id, customer_id, proposed_price=120, min_price=100)

    sales_headers = auth_headers(client, "sales.1")
    so_resp = client.post(
        "/api/v1/sales-orders",
        headers=sales_headers,
        json={
            "customer_id": customer_id,
            "product_id": product_id,
            "price_list_id": price_list_id,
            "order_date": "2026-09-22",
            "qty": 10,
            "unit_price": 120,
            "actor": "sales.1",
            "actor_role": "Sales Officer",
        },
    )
    assert so_resp.status_code == 201, so_resp.text
    so_id = so_resp.json()["id"]

    confirm_resp = client.post(
        f"/api/v1/sales-orders/{so_id}/confirm",
        headers=auth_headers(client, "sales.mgr"),
        json={"actor": "sales.mgr", "actor_role": "Sales Manager", "note": "check credit"},
    )
    assert confirm_resp.status_code == 409, confirm_resp.text
    assert "SAL-001" in confirm_resp.json()["detail"]

    alerts_resp = client.get("/api/v1/alerts", headers=auth_headers(client, "sales.mgr"))
    assert alerts_resp.status_code == 200, alerts_resp.text
    assert any(alert["alert_code"] == "CREDIT-LIMIT" for alert in alerts_resp.json())


def test_sales_below_floor_creates_alert_and_requires_manager_confirmation(client: TestClient) -> None:
    customer_id = create_customer(client, "CUS-300", 10000)
    product_id = create_product(client, "PRD-300", min_price=120)
    price_list_id = create_price_list(client, product_id, customer_id, proposed_price=150, min_price=120)

    sales_headers = auth_headers(client, "sales.1")
    so_resp = client.post(
        "/api/v1/sales-orders",
        headers=sales_headers,
        json={
            "customer_id": customer_id,
            "product_id": product_id,
            "price_list_id": price_list_id,
            "order_date": "2026-09-22",
            "qty": 5,
            "unit_price": 110,
            "actor": "sales.1",
            "actor_role": "Sales Officer",
        },
    )
    assert so_resp.status_code == 201, so_resp.text
    so_id = so_resp.json()["id"]
    assert so_resp.json()["pricing_status"] == "below_floor"

    alerts_resp = client.get("/api/v1/alerts", headers=auth_headers(client, "sales.mgr"))
    assert alerts_resp.status_code == 200, alerts_resp.text
    assert any(alert["alert_code"] == "SALES-BELOW-FLOOR" for alert in alerts_resp.json())

    confirm_resp = client.post(
        f"/api/v1/sales-orders/{so_id}/confirm",
        headers=auth_headers(client, "sales.mgr"),
        json={"actor": "sales.mgr", "actor_role": "Sales Manager", "note": "approve below floor"},
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    assert confirm_resp.json()["status"] == "sales_order_confirmed"


def create_confirmed_sales_order(client: TestClient, code: str, *, credit_limit: float = 10000, unit_price: float = 150, min_price: float = 120, qty: float = 10) -> tuple[int, float]:
    customer_id = create_customer(client, f"CUS-{code}", credit_limit)
    product_id = create_product(client, f"PRD-{code}", min_price=min_price)
    price_list_id = create_price_list(client, product_id, customer_id, proposed_price=unit_price, min_price=min_price)

    so_resp = client.post(
        "/api/v1/sales-orders",
        headers=auth_headers(client, "sales.1"),
        json={
            "customer_id": customer_id,
            "product_id": product_id,
            "price_list_id": price_list_id,
            "order_date": "2026-09-22",
            "requested_delivery_date": "2026-09-30",
            "qty": qty,
            "unit_price": unit_price,
            "actor": "sales.1",
            "actor_role": "Sales Officer",
        },
    )
    assert so_resp.status_code == 201, so_resp.text
    so_id = so_resp.json()["id"]

    confirm_resp = client.post(
        f"/api/v1/sales-orders/{so_id}/confirm",
        headers=auth_headers(client, "sales.mgr"),
        json={"actor": "sales.mgr", "actor_role": "Sales Manager", "note": "confirmed"},
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    return so_id, float(qty * unit_price)


def test_sales_fulfillment_end_to_end_to_closure(client: TestClient) -> None:
    so_id, total_amount = create_confirmed_sales_order(client, "400")

    delivery_resp = client.post(
        "/api/v1/sales-deliveries",
        headers=auth_headers(client, "planning.1"),
        json={
            "sales_order_id": so_id,
            "planned_date": "2026-09-23",
            "warehouse_code": "FG-01",
            "planned_qty": 10,
            "actor": "planning.1",
            "actor_role": "Planning Officer",
        },
    )
    assert delivery_resp.status_code == 201, delivery_resp.text
    delivery_id = delivery_resp.json()["id"]
    assert delivery_resp.json()["status"] == "planning_allocation"

    release_resp = client.post(
        f"/api/v1/sales-deliveries/{delivery_id}/release",
        headers=auth_headers(client, "planning.1"),
        json={
            "actor": "planning.1",
            "actor_role": "Planning Officer",
            "release_date": "2026-09-24",
            "note": "stock allocated",
        },
    )
    assert release_resp.status_code == 200, release_resp.text
    assert release_resp.json()["status"] == "ready_to_deliver"

    deliver_resp = client.post(
        f"/api/v1/sales-deliveries/{delivery_id}/deliver",
        headers=auth_headers(client, "logistics.1"),
        json={
            "actor": "logistics.1",
            "actor_role": "Logistics Officer",
            "delivered_date": "2026-09-25",
            "delivered_qty": 10,
            "dispatch_reference": "LR-400",
            "note": "delivered to customer",
        },
    )
    assert deliver_resp.status_code == 200, deliver_resp.text
    assert deliver_resp.json()["status"] == "delivered"

    invoice_resp = client.post(
        "/api/v1/sales-invoices",
        headers=auth_headers(client, "ar.1"),
        json={
            "sales_order_id": so_id,
            "sales_delivery_id": delivery_id,
            "invoice_no": "SI-400",
            "invoice_date": "2026-09-26",
            "due_date": "2026-10-26",
            "currency": "IRR",
            "total_amount": total_amount,
            "actor": "ar.1",
            "actor_role": "AR Accountant",
        },
    )
    assert invoice_resp.status_code == 201, invoice_resp.text
    invoice_id = invoice_resp.json()["id"]
    assert invoice_resp.json()["status"] == "collection_open"

    partial_collection = client.post(
        "/api/v1/collections",
        headers=auth_headers(client, "collect.1"),
        json={
            "sales_invoice_id": invoice_id,
            "receipt_date": "2026-10-01",
            "amount": 500,
            "currency": "IRR",
            "payment_method": "wire",
            "bank_reference": "COL-400-A",
            "actor": "collect.1",
            "actor_role": "Collections Officer",
        },
    )
    assert partial_collection.status_code == 201, partial_collection.text

    invoice_state = client.get(f"/api/v1/sales-invoices/{invoice_id}", headers=auth_headers(client, "ar.1"))
    assert invoice_state.status_code == 200, invoice_state.text
    assert invoice_state.json()["collection_status"] == "partial"

    final_collection = client.post(
        "/api/v1/collections",
        headers=auth_headers(client, "collect.1"),
        json={
            "sales_invoice_id": invoice_id,
            "receipt_date": "2026-10-10",
            "amount": total_amount - 500,
            "currency": "IRR",
            "payment_method": "wire",
            "bank_reference": "COL-400-B",
            "actor": "collect.1",
            "actor_role": "Collections Officer",
        },
    )
    assert final_collection.status_code == 201, final_collection.text

    review_resp = client.post(
        f"/api/v1/sales-orders/{so_id}/review-profitability",
        headers=auth_headers(client, "pricing.1"),
        json={"actor": "pricing.1", "actor_role": "Pricing Analyst", "note": "margin reviewed"},
    )
    assert review_resp.status_code == 200, review_resp.text
    assert review_resp.json()["status"] == "profitability_reviewed"

    close_resp = client.post(
        f"/api/v1/sales-orders/{so_id}/close",
        headers=auth_headers(client, "sales.mgr"),
        json={"actor": "sales.mgr", "actor_role": "Sales Manager", "note": "case closed"},
    )
    assert close_resp.status_code == 200, close_resp.text
    assert close_resp.json()["status"] == "closed"

    dashboard_resp = client.get("/api/v1/dashboard/summary", headers=auth_headers(client, "sales.mgr"))
    assert dashboard_resp.status_code == 200, dashboard_resp.text
    body = dashboard_resp.json()
    assert body["sales_deliveries_by_status"].get("delivered", 0) >= 1
    assert body["sales_invoices_by_status"].get("collected", 0) >= 1
    assert body["collections_by_status"].get("collected", 0) >= 2


def test_sales_invoice_before_delivery_is_blocked(client: TestClient) -> None:
    so_id, total_amount = create_confirmed_sales_order(client, "500")

    delivery_resp = client.post(
        "/api/v1/sales-deliveries",
        headers=auth_headers(client, "planning.1"),
        json={
            "sales_order_id": so_id,
            "planned_date": "2026-09-23",
            "warehouse_code": "FG-02",
            "planned_qty": 10,
            "actor": "planning.1",
            "actor_role": "Planning Officer",
        },
    )
    assert delivery_resp.status_code == 201, delivery_resp.text
    delivery_id = delivery_resp.json()["id"]

    invoice_resp = client.post(
        "/api/v1/sales-invoices",
        headers=auth_headers(client, "ar.1"),
        json={
            "sales_order_id": so_id,
            "sales_delivery_id": delivery_id,
            "invoice_no": "SI-500",
            "invoice_date": "2026-09-26",
            "currency": "IRR",
            "total_amount": total_amount,
            "actor": "ar.1",
            "actor_role": "AR Accountant",
        },
    )
    assert invoice_resp.status_code == 409, invoice_resp.text
    assert "DEL-001" in invoice_resp.json()["detail"]



def test_collection_cannot_exceed_invoice_open_amount(client: TestClient) -> None:
    so_id, total_amount = create_confirmed_sales_order(client, "600")

    delivery_resp = client.post(
        "/api/v1/sales-deliveries",
        headers=auth_headers(client, "planning.1"),
        json={
            "sales_order_id": so_id,
            "planned_date": "2026-09-23",
            "warehouse_code": "FG-03",
            "planned_qty": 10,
            "actor": "planning.1",
            "actor_role": "Planning Officer",
        },
    )
    delivery_id = delivery_resp.json()["id"]
    client.post(
        f"/api/v1/sales-deliveries/{delivery_id}/release",
        headers=auth_headers(client, "planning.1"),
        json={"actor": "planning.1", "actor_role": "Planning Officer", "release_date": "2026-09-24"},
    )
    client.post(
        f"/api/v1/sales-deliveries/{delivery_id}/deliver",
        headers=auth_headers(client, "logistics.1"),
        json={
            "actor": "logistics.1",
            "actor_role": "Logistics Officer",
            "delivered_date": "2026-09-25",
            "delivered_qty": 10,
            "dispatch_reference": "LR-600",
        },
    )
    invoice_resp = client.post(
        "/api/v1/sales-invoices",
        headers=auth_headers(client, "ar.1"),
        json={
            "sales_order_id": so_id,
            "sales_delivery_id": delivery_id,
            "invoice_no": "SI-600",
            "invoice_date": "2026-09-26",
            "currency": "IRR",
            "total_amount": total_amount,
            "actor": "ar.1",
            "actor_role": "AR Accountant",
        },
    )
    assert invoice_resp.status_code == 201, invoice_resp.text
    invoice_id = invoice_resp.json()["id"]

    first_collection = client.post(
        "/api/v1/collections",
        headers=auth_headers(client, "collect.1"),
        json={
            "sales_invoice_id": invoice_id,
            "receipt_date": "2026-10-01",
            "amount": total_amount - 100,
            "currency": "IRR",
            "payment_method": "wire",
            "bank_reference": "COL-600-A",
            "actor": "collect.1",
            "actor_role": "Collections Officer",
        },
    )
    assert first_collection.status_code == 201, first_collection.text

    second_collection = client.post(
        "/api/v1/collections",
        headers=auth_headers(client, "collect.1"),
        json={
            "sales_invoice_id": invoice_id,
            "receipt_date": "2026-10-02",
            "amount": 200,
            "currency": "IRR",
            "payment_method": "wire",
            "bank_reference": "COL-600-B",
            "actor": "collect.1",
            "actor_role": "Collections Officer",
        },
    )
    assert second_collection.status_code == 409, second_collection.text
    assert "COL-001" in second_collection.json()["detail"]


def test_sales_traceability_for_delivery_invoice_collection_chain(client: TestClient) -> None:
    so_id, total_amount = create_confirmed_sales_order(client, "700")

    delivery_resp = client.post(
        "/api/v1/sales-deliveries",
        headers=auth_headers(client, "planning.1"),
        json={
            "sales_order_id": so_id,
            "planned_date": "2026-09-23",
            "warehouse_code": "FG-04",
            "planned_qty": 10,
            "actor": "planning.1",
            "actor_role": "Planning Officer",
        },
    )
    assert delivery_resp.status_code == 201, delivery_resp.text
    delivery_id = delivery_resp.json()["id"]

    assert client.post(
        f"/api/v1/sales-deliveries/{delivery_id}/release",
        headers=auth_headers(client, "planning.1"),
        json={"actor": "planning.1", "actor_role": "Planning Officer", "release_date": "2026-09-24", "note": "release for trace"},
    ).status_code == 200
    assert client.post(
        f"/api/v1/sales-deliveries/{delivery_id}/deliver",
        headers=auth_headers(client, "logistics.1"),
        json={
            "actor": "logistics.1",
            "actor_role": "Logistics Officer",
            "delivered_date": "2026-09-25",
            "delivered_qty": 10,
            "dispatch_reference": "LR-700",
            "note": "delivered for trace",
        },
    ).status_code == 200

    invoice_resp = client.post(
        "/api/v1/sales-invoices",
        headers=auth_headers(client, "ar.1"),
        json={
            "sales_order_id": so_id,
            "sales_delivery_id": delivery_id,
            "invoice_no": "SI-700",
            "invoice_date": "2026-09-26",
            "due_date": "2026-10-26",
            "currency": "IRR",
            "total_amount": total_amount,
            "actor": "ar.1",
            "actor_role": "AR Accountant",
        },
    )
    assert invoice_resp.status_code == 201, invoice_resp.text
    invoice_id = invoice_resp.json()["id"]

    collection_resp = client.post(
        "/api/v1/collections",
        headers=auth_headers(client, "collect.1"),
        json={
            "sales_invoice_id": invoice_id,
            "receipt_date": "2026-10-01",
            "amount": total_amount,
            "currency": "IRR",
            "payment_method": "wire",
            "bank_reference": "COL-700",
            "actor": "collect.1",
            "actor_role": "Collections Officer",
        },
    )
    assert collection_resp.status_code == 201, collection_resp.text
    collection_id = collection_resp.json()["id"]

    trace_resp = client.get(f"/api/v1/traceability/sales-orders/{so_id}", headers=auth_headers(client, "sales.mgr"))
    assert trace_resp.status_code == 200, trace_resp.text
    payload = trace_resp.json()
    assert payload["overview"]["process_name"] == "sales"
    assert payload["overview"]["root_object_type"] == "SalesOrder"
    assert payload["overview"]["root_object_id"] == so_id
    assert payload["overview"]["linked_document_count"] >= 5
    assert any(doc["object_type"] == "PriceList" for doc in payload["linked_documents"])
    assert any(doc["object_type"] == "SalesDelivery" for doc in payload["linked_documents"])
    assert any(doc["object_type"] == "SalesInvoice" for doc in payload["linked_documents"])
    assert any(doc["object_type"] == "CollectionReceipt" for doc in payload["linked_documents"])
    assert any(item["event_type"].startswith("approval:") for item in payload["timeline"])

    doc_trace_resp = client.get(
        f"/api/v1/traceability/document/collection/{collection_id}",
        headers=auth_headers(client, "collect.1"),
    )
    assert doc_trace_resp.status_code == 200, doc_trace_resp.text
    doc_payload = doc_trace_resp.json()
    assert doc_payload["overview"]["root_object_id"] == so_id
    assert doc_payload["overview"]["process_name"] == "sales"


def test_security_headers_present_on_api_responses(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200, resp.text
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "same-origin"
    assert "camera=()" in resp.headers["permissions-policy"]
    assert resp.headers["cache-control"] == "no-store"
