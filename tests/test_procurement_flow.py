from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.models.workflow import WorkflowInstance


def auth_headers(client: TestClient, username: str) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": username})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_supplier(client: TestClient, code: str, *, approval_status: str = "approved") -> int:
    resp = client.post(
        "/api/v1/suppliers",
        headers=auth_headers(client, "master.admin"),
        json={
            "code": code,
            "name": f"Supplier {code}",
            "approval_status": approval_status,
            "risk_level": "medium",
            "payment_terms": "30D",
            "created_by": "master.admin",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def create_approved_pr(client: TestClient) -> int:
    requester_headers = auth_headers(client, "sara")
    pr_resp = client.post(
        "/api/v1/purchase-requests",
        headers=requester_headers,
        json={
            "requester": "sara",
            "department": "production",
            "reason": "industrial resin needed",
            "cost_center_code": "CC-500",
            "budget_status": "within_budget",
            "priority": "high",
            "total_estimated_amount": 9000,
            "currency": "IRR",
            "lines": [
                {
                    "line_no": 1,
                    "description": "resin batch",
                    "qty": 3,
                    "uom": "ton",
                    "estimated_unit_price": 3000,
                    "cost_center_code": "CC-500",
                }
            ],
        },
    )
    assert pr_resp.status_code == 201, pr_resp.text
    pr_id = pr_resp.json()["id"]
    assert client.post(
        f"/api/v1/purchase-requests/{pr_id}/submit",
        headers=requester_headers,
        json={"actor": "sara", "actor_role": "Requester", "exception_approved": False},
    ).status_code == 200
    manager_headers = auth_headers(client, "manager.1")
    assert client.post(
        f"/api/v1/purchase-requests/{pr_id}/route-review",
        headers=manager_headers,
        json={"actor": "manager.1", "actor_role": "Department Manager", "note": "reviewed"},
    ).status_code == 200
    approve_resp = client.post(
        f"/api/v1/purchase-requests/{pr_id}/approve",
        headers=manager_headers,
        json={"actor": "manager.1", "actor_role": "Department Manager", "note": "approved"},
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "approved"
    return pr_id


def create_price_approved_rfq(client: TestClient, supplier_ids: list[int]) -> tuple[int, int]:
    buyer_headers = auth_headers(client, "buyer.1")
    pr_id = create_approved_pr(client)
    rfq_resp = client.post(
        "/api/v1/rfqs",
        headers=buyer_headers,
        json={
            "purchase_request_id": pr_id,
            "issue_date": "2026-09-22",
            "close_date": "2026-09-25",
            "minimum_quote_count": 3,
            "buyer": "buyer.1",
            "created_by": "buyer.1",
        },
    )
    assert rfq_resp.status_code == 201, rfq_resp.text
    rfq_id = rfq_resp.json()["id"]

    quote_ids: list[int] = []
    for idx, supplier_id in enumerate(supplier_ids, start=1):
        q_resp = client.post(
            f"/api/v1/rfqs/{rfq_id}/quotations",
            headers=buyer_headers,
            json={
                "supplier_id": supplier_id,
                "quote_no": f"Q-{rfq_id}-{idx}",
                "quote_date": "2026-09-22",
                "currency": "IRR",
                "validity_date": "2026-10-01",
                "delivery_days": 7 + idx,
                "payment_terms": "30D",
                "total_amount": 8000 + idx * 100,
                "price_variance_pct": 1.5,
                "commercial_score": 80 + idx,
                "technical_score": 85 + idx,
                "created_by": "buyer.1",
            },
        )
        assert q_resp.status_code == 201, q_resp.text
        quote_ids.append(q_resp.json()["id"])

    record_quotes_resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/record-quotes",
        headers=buyer_headers,
        json={"actor": "buyer.1", "actor_role": "Procurement Officer", "exception_approved": False},
    )
    assert record_quotes_resp.status_code == 200, record_quotes_resp.text

    comm_resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/commercial-evaluate",
        headers=buyer_headers,
        json={
            "actor": "buyer.1",
            "actor_role": "Procurement Officer",
            "selected_quotation_id": quote_ids[0],
            "note": "best commercial offer",
        },
    )
    assert comm_resp.status_code == 200, comm_resp.text

    tech_resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/technical-approve",
        headers=auth_headers(client, "tech.1"),
        json={"actor": "tech.1", "actor_role": "Technical Evaluator", "note": "approved technically"},
    )
    assert tech_resp.status_code == 200, tech_resp.text

    price_resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/price-approve",
        headers=auth_headers(client, "proc.mgr"),
        json={"actor": "proc.mgr", "actor_role": "Procurement Manager", "note": "price approved"},
    )
    assert price_resp.status_code == 200, price_resp.text
    return rfq_id, quote_ids[0]


def create_po(client: TestClient, *, supplier_status: str = "approved") -> tuple[int, int]:
    supplier_ids = [create_supplier(client, f"SUP-{suffix}", approval_status=supplier_status) for suffix in [100, 101, 102]]
    rfq_id, selected_quote_id = create_price_approved_rfq(client, supplier_ids)
    po_resp = client.post(
        "/api/v1/purchase-orders",
        headers=auth_headers(client, "buyer.1"),
        json={
            "rfq_id": rfq_id,
            "selected_quotation_id": selected_quote_id,
            "order_date": "2026-09-23",
            "delivery_date": "2026-09-30",
            "emergency_flag": False,
            "actor": "buyer.1",
            "actor_role": "Procurement Officer",
            "exception_approved": False,
            "note": "issue PO",
        },
    )
    assert po_resp.status_code == 201, po_resp.text
    return po_resp.json()["id"], supplier_ids[0]


def test_rfq_to_po_end_to_end(client: TestClient) -> None:
    po_id, _ = create_po(client)
    po_resp = client.get(f"/api/v1/purchase-orders/{po_id}", headers=auth_headers(client, "buyer.1"))
    assert po_resp.status_code == 200
    assert po_resp.json()["status"] == "po_issued"


def test_rfq_creation_blocked_before_pr_approval(client: TestClient) -> None:
    requester_headers = auth_headers(client, "mina")
    pr_resp = client.post(
        "/api/v1/purchase-requests",
        headers=requester_headers,
        json={
            "requester": "mina",
            "department": "engineering",
            "reason": "instrument replacement",
            "cost_center_code": "CC-700",
            "budget_status": "within_budget",
            "priority": "normal",
            "total_estimated_amount": 1500,
            "currency": "IRR",
            "lines": [
                {
                    "line_no": 1,
                    "description": "sensor",
                    "qty": 1,
                    "uom": "pcs",
                    "estimated_unit_price": 1500,
                    "cost_center_code": "CC-700",
                }
            ],
        },
    )
    assert pr_resp.status_code == 201, pr_resp.text
    pr_id = pr_resp.json()["id"]

    blocked_rfq = client.post(
        "/api/v1/rfqs",
        headers=auth_headers(client, "buyer.2"),
        json={
            "purchase_request_id": pr_id,
            "issue_date": "2026-09-22",
            "minimum_quote_count": 3,
            "buyer": "buyer.2",
        },
    )
    assert blocked_rfq.status_code == 409, blocked_rfq.text
    assert "RFQ-001" in blocked_rfq.json()["detail"]


def test_receipt_qc_invoice_payment_end_to_end(client: TestClient) -> None:
    po_id, supplier_id = create_po(client)

    receipt_resp = client.post(
        "/api/v1/goods-receipts",
        headers=auth_headers(client, "warehouse.1"),
        json={
            "purchase_order_id": po_id,
            "receipt_date": "2026-09-24",
            "warehouse_code": "WH-01",
            "supplier_delivery_ref": "DLV-001",
            "received_qty": 3,
            "actor": "warehouse.1",
            "actor_role": "Warehouse Receiver",
        },
    )
    assert receipt_resp.status_code == 201, receipt_resp.text
    receipt_id = receipt_resp.json()["id"]

    qc_create_resp = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(client, "qc.1"),
        json={
            "goods_receipt_id": receipt_id,
            "inspection_date": "2026-09-24",
            "inspector": "qc.1",
            "actor_role": "QC Inspector",
        },
    )
    assert qc_create_resp.status_code == 201, qc_create_resp.text
    qc_id = qc_create_resp.json()["id"]

    qc_finalize_resp = client.post(
        f"/api/v1/quality-inspections/{qc_id}/finalize",
        headers=auth_headers(client, "qc.1"),
        json={
            "actor": "qc.1",
            "actor_role": "QC Inspector",
            "result": "accepted",
            "accepted_qty": 3,
            "rejected_qty": 0,
            "note": "passed qc",
        },
    )
    assert qc_finalize_resp.status_code == 200, qc_finalize_resp.text
    assert qc_finalize_resp.json()["status"] == "inventory_released"

    invoice_resp = client.post(
        "/api/v1/supplier-invoices",
        headers=auth_headers(client, "ap.1"),
        json={
            "supplier_id": supplier_id,
            "purchase_order_id": po_id,
            "goods_receipt_id": receipt_id,
            "invoice_no": "SUP-INV-001",
            "invoice_date": "2026-09-25",
            "due_date": "2026-10-05",
            "currency": "IRR",
            "total_amount": 8100,
            "actor": "ap.1",
            "actor_role": "AP Accountant",
        },
    )
    assert invoice_resp.status_code == 201, invoice_resp.text
    invoice_id = invoice_resp.json()["id"]

    match_resp = client.post(
        f"/api/v1/supplier-invoices/{invoice_id}/match",
        headers=auth_headers(client, "ap.1"),
        json={"actor": "ap.1", "actor_role": "AP Accountant", "note": "3-way match ok"},
    )
    assert match_resp.status_code == 200, match_resp.text
    assert match_resp.json()["match_status"] == "matched"

    payment_resp = client.post(
        "/api/v1/payments",
        headers=auth_headers(client, "ap.1"),
        json={
            "supplier_invoice_id": invoice_id,
            "payment_date": "2026-09-27",
            "amount": 8100,
            "currency": "IRR",
            "payment_method": "bank-transfer",
            "bank_reference": "BT-001",
            "actor": "ap.1",
            "actor_role": "AP Accountant",
        },
    )
    assert payment_resp.status_code == 201, payment_resp.text
    payment_id = payment_resp.json()["id"]

    approve_payment_resp = client.post(
        f"/api/v1/payments/{payment_id}/approve",
        headers=auth_headers(client, "finance.1"),
        json={"actor": "finance.1", "actor_role": "Finance Manager", "note": "approved"},
    )
    assert approve_payment_resp.status_code == 200, approve_payment_resp.text
    assert approve_payment_resp.json()["status"] == "payment_approved"

    execute_payment_resp = client.post(
        f"/api/v1/payments/{payment_id}/execute",
        headers=auth_headers(client, "treasury.1"),
        json={"actor": "treasury.1", "actor_role": "Treasury Officer", "note": "paid"},
    )
    assert execute_payment_resp.status_code == 200, execute_payment_resp.text
    assert execute_payment_resp.json()["status"] == "paid"


def test_invoice_match_blocked_when_qc_rejected(client: TestClient) -> None:
    po_id, supplier_id = create_po(client)

    receipt_resp = client.post(
        "/api/v1/goods-receipts",
        headers=auth_headers(client, "warehouse.2"),
        json={
            "purchase_order_id": po_id,
            "receipt_date": "2026-09-24",
            "warehouse_code": "WH-02",
            "supplier_delivery_ref": "DLV-REJ",
            "received_qty": 3,
            "actor": "warehouse.2",
            "actor_role": "Warehouse Receiver",
        },
    )
    assert receipt_resp.status_code == 201, receipt_resp.text
    receipt_id = receipt_resp.json()["id"]

    qc_create_resp = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(client, "qc.2"),
        json={
            "goods_receipt_id": receipt_id,
            "inspection_date": "2026-09-24",
            "inspector": "qc.2",
            "actor_role": "QC Inspector",
        },
    )
    assert qc_create_resp.status_code == 201, qc_create_resp.text
    qc_id = qc_create_resp.json()["id"]

    qc_finalize_resp = client.post(
        f"/api/v1/quality-inspections/{qc_id}/finalize",
        headers=auth_headers(client, "qc.2"),
        json={
            "actor": "qc.2",
            "actor_role": "QC Inspector",
            "result": "rejected",
            "accepted_qty": 0,
            "rejected_qty": 3,
            "defect_code": "DEF-01",
            "corrective_action": "return to supplier",
            "note": "failed qc",
        },
    )
    assert qc_finalize_resp.status_code == 200, qc_finalize_resp.text
    assert qc_finalize_resp.json()["status"] == "rejected"

    invoice_resp = client.post(
        "/api/v1/supplier-invoices",
        headers=auth_headers(client, "ap.2"),
        json={
            "supplier_id": supplier_id,
            "purchase_order_id": po_id,
            "goods_receipt_id": receipt_id,
            "invoice_no": "SUP-INV-REJ",
            "invoice_date": "2026-09-25",
            "currency": "IRR",
            "total_amount": 8100,
            "actor": "ap.2",
            "actor_role": "AP Accountant",
        },
    )
    assert invoice_resp.status_code == 201, invoice_resp.text
    invoice_id = invoice_resp.json()["id"]

    match_resp = client.post(
        f"/api/v1/supplier-invoices/{invoice_id}/match",
        headers=auth_headers(client, "ap.2"),
        json={"actor": "ap.2", "actor_role": "AP Accountant", "note": "attempt match"},
    )
    assert match_resp.status_code == 409, match_resp.text
    assert "INV-001" in match_resp.json()["detail"]


def test_payment_creation_blocked_before_invoice_match(client: TestClient) -> None:
    po_id, supplier_id = create_po(client)

    receipt_resp = client.post(
        "/api/v1/goods-receipts",
        headers=auth_headers(client, "warehouse.3"),
        json={
            "purchase_order_id": po_id,
            "receipt_date": "2026-09-24",
            "warehouse_code": "WH-03",
            "supplier_delivery_ref": "DLV-PREPAY",
            "received_qty": 3,
            "actor": "warehouse.3",
            "actor_role": "Warehouse Receiver",
        },
    )
    assert receipt_resp.status_code == 201, receipt_resp.text
    receipt_id = receipt_resp.json()["id"]

    qc_create_resp = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(client, "qc.3"),
        json={
            "goods_receipt_id": receipt_id,
            "inspection_date": "2026-09-24",
            "inspector": "qc.3",
            "actor_role": "QC Inspector",
        },
    )
    qc_id = qc_create_resp.json()["id"]
    assert client.post(
        f"/api/v1/quality-inspections/{qc_id}/finalize",
        headers=auth_headers(client, "qc.3"),
        json={
            "actor": "qc.3",
            "actor_role": "QC Inspector",
            "result": "accepted",
            "accepted_qty": 3,
            "rejected_qty": 0,
            "note": "passed qc",
        },
    ).status_code == 200

    invoice_resp = client.post(
        "/api/v1/supplier-invoices",
        headers=auth_headers(client, "ap.3"),
        json={
            "supplier_id": supplier_id,
            "purchase_order_id": po_id,
            "goods_receipt_id": receipt_id,
            "invoice_no": "SUP-INV-PREPAY",
            "invoice_date": "2026-09-25",
            "currency": "IRR",
            "total_amount": 8100,
            "actor": "ap.3",
            "actor_role": "AP Accountant",
        },
    )
    assert invoice_resp.status_code == 201, invoice_resp.text
    invoice_id = invoice_resp.json()["id"]

    payment_resp = client.post(
        "/api/v1/payments",
        headers=auth_headers(client, "ap.3"),
        json={
            "supplier_invoice_id": invoice_id,
            "payment_date": "2026-09-27",
            "amount": 8100,
            "currency": "IRR",
            "payment_method": "bank-transfer",
            "actor": "ap.3",
            "actor_role": "AP Accountant",
        },
    )
    assert payment_resp.status_code == 409, payment_resp.text
    assert "PAY-001" in payment_resp.json()["detail"]


def test_approval_inbox_and_role_protection(client: TestClient) -> None:
    pr_id = create_approved_pr(client)
    rfq_headers = auth_headers(client, "buyer.1")
    rfq_resp = client.post(
        "/api/v1/rfqs",
        headers=rfq_headers,
        json={
            "purchase_request_id": pr_id,
            "issue_date": "2026-09-22",
            "close_date": "2026-09-25",
            "minimum_quote_count": 1,
            "buyer": "buyer.1",
            "created_by": "buyer.1",
        },
    )
    assert rfq_resp.status_code == 201, rfq_resp.text
    rfq_id = rfq_resp.json()["id"]

    quote_resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/quotations",
        headers=rfq_headers,
        json={
            "supplier_id": create_supplier(client, "SUP-ROLE"),
            "quote_no": "ROLE-Q-1",
            "quote_date": "2026-09-22",
            "currency": "IRR",
            "total_amount": 5000,
            "created_by": "buyer.1",
        },
    )
    assert quote_resp.status_code == 201, quote_resp.text

    record_resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/record-quotes",
        headers=rfq_headers,
        json={"actor": "buyer.1", "actor_role": "Procurement Officer", "exception_approved": True},
    )
    assert record_resp.status_code == 200, record_resp.text

    comm_resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/commercial-evaluate",
        headers=rfq_headers,
        json={
            "actor": "buyer.1",
            "actor_role": "Procurement Officer",
            "selected_quotation_id": quote_resp.json()["id"],
        },
    )
    assert comm_resp.status_code == 200, comm_resp.text

    inbox_resp = client.get("/api/v1/inbox/approvals", headers=auth_headers(client, "tech.1"))
    assert inbox_resp.status_code == 200, inbox_resp.text
    assert any(item["object_type"] == "RFQ" and "technical_eval" in item["available_actions"] for item in inbox_resp.json())

    forbidden_resp = client.post(
        f"/api/v1/rfqs/{rfq_id}/technical-approve",
        headers=rfq_headers,
        json={"actor": "buyer.1", "actor_role": "Procurement Officer", "note": "illegal"},
    )
    assert forbidden_resp.status_code == 403, forbidden_resp.text


def test_traceability_view_for_procurement_chain(client: TestClient) -> None:
    po_id, supplier_id = create_po(client)

    receipt_resp = client.post(
        "/api/v1/goods-receipts",
        headers=auth_headers(client, "warehouse.1"),
        json={
            "purchase_order_id": po_id,
            "receipt_date": "2026-09-24",
            "warehouse_code": "WH-T1",
            "supplier_delivery_ref": "DLV-T1",
            "received_qty": 3,
            "actor": "warehouse.1",
            "actor_role": "Warehouse Receiver",
        },
    )
    receipt_id = receipt_resp.json()["id"]

    qc_create_resp = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(client, "qc.1"),
        json={
            "goods_receipt_id": receipt_id,
            "inspection_date": "2026-09-24",
            "inspector": "qc.1",
            "actor_role": "QC Inspector",
        },
    )
    qc_id = qc_create_resp.json()["id"]
    assert client.post(
        f"/api/v1/quality-inspections/{qc_id}/finalize",
        headers=auth_headers(client, "qc.1"),
        json={
            "actor": "qc.1",
            "actor_role": "QC Inspector",
            "result": "accepted",
            "accepted_qty": 3,
            "rejected_qty": 0,
            "note": "traceability qc pass",
        },
    ).status_code == 200

    invoice_resp = client.post(
        "/api/v1/supplier-invoices",
        headers=auth_headers(client, "ap.1"),
        json={
            "supplier_id": supplier_id,
            "purchase_order_id": po_id,
            "goods_receipt_id": receipt_id,
            "invoice_no": "SUP-INV-TRACE",
            "invoice_date": "2026-09-25",
            "currency": "IRR",
            "total_amount": 8100,
            "actor": "ap.1",
            "actor_role": "AP Accountant",
        },
    )
    invoice_id = invoice_resp.json()["id"]
    assert client.post(
        f"/api/v1/supplier-invoices/{invoice_id}/match",
        headers=auth_headers(client, "ap.1"),
        json={"actor": "ap.1", "actor_role": "AP Accountant", "note": "traceability match"},
    ).status_code == 200

    payment_resp = client.post(
        "/api/v1/payments",
        headers=auth_headers(client, "ap.1"),
        json={
            "supplier_invoice_id": invoice_id,
            "payment_date": "2026-09-27",
            "amount": 8100,
            "currency": "IRR",
            "payment_method": "bank-transfer",
            "actor": "ap.1",
            "actor_role": "AP Accountant",
        },
    )
    payment_id = payment_resp.json()["id"]
    assert client.post(
        f"/api/v1/payments/{payment_id}/approve",
        headers=auth_headers(client, "finance.1"),
        json={"actor": "finance.1", "actor_role": "Finance Manager", "note": "traceability approve"},
    ).status_code == 200

    po_detail_resp = client.get(f"/api/v1/purchase-orders/{po_id}", headers=auth_headers(client, "buyer.1"))
    pr_id = po_detail_resp.json()["purchase_request_id"]

    trace_resp = client.get(f"/api/v1/traceability/purchase-requests/{pr_id}", headers=auth_headers(client, "manager.1"))
    assert trace_resp.status_code == 200, trace_resp.text
    payload = trace_resp.json()
    assert payload["overview"]["root_object_type"] == "PurchaseRequest"
    assert payload["overview"]["active_object_type"] == "Payment"
    assert payload["overview"]["linked_document_count"] >= 8
    assert any(doc["object_type"] == "RFQ" for doc in payload["linked_documents"])
    assert any(doc["object_type"] == "Payment" for doc in payload["linked_documents"])
    assert any(item["event_type"].startswith("approval:") for item in payload["timeline"])

    doc_trace_resp = client.get(
        f"/api/v1/traceability/document/payment/{payment_id}",
        headers=auth_headers(client, "finance.1"),
    )
    assert doc_trace_resp.status_code == 200, doc_trace_resp.text
    doc_payload = doc_trace_resp.json()
    assert doc_payload["overview"]["root_object_id"] == pr_id
    assert doc_payload["overview"]["active_object_code"] == payload["overview"]["active_object_code"]


def test_scheduler_creates_alerts_and_escalation_dashboard(client: TestClient) -> None:
    requester_headers = auth_headers(client, "ali")
    pr_resp = client.post(
        "/api/v1/purchase-requests",
        headers=requester_headers,
        json={
            "requester": "ali",
            "department": "ops",
            "reason": "overdue review test",
            "cost_center_code": "CC-900",
            "budget_status": "within_budget",
            "priority": "normal",
            "total_estimated_amount": 100,
            "currency": "IRR",
            "lines": [
                {
                    "line_no": 1,
                    "description": "test item",
                    "qty": 1,
                    "uom": "pcs",
                    "estimated_unit_price": 100,
                    "cost_center_code": "CC-900",
                }
            ],
        },
    )
    pr_id = pr_resp.json()["id"]
    assert client.post(
        f"/api/v1/purchase-requests/{pr_id}/submit",
        headers=requester_headers,
        json={"actor": "ali", "actor_role": "Requester", "exception_approved": False},
    ).status_code == 200

    manager_headers = auth_headers(client, "manager.1")
    route_resp = client.post(
        f"/api/v1/purchase-requests/{pr_id}/route-review",
        headers=manager_headers,
        json={"actor": "manager.1", "actor_role": "Department Manager", "note": "queued"},
    )
    assert route_resp.status_code == 200, route_resp.text
    workflow_instance_id = route_resp.json()["workflow_instance_id"]

    db = SessionLocal()
    try:
        instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == workflow_instance_id).first()
        assert instance is not None
        instance.due_at = (datetime.now(UTC) - timedelta(hours=10)).isoformat()
        db.commit()
    finally:
        db.close()

    scheduler_resp = client.post("/api/v1/scheduler/run-sla", headers=manager_headers)
    assert scheduler_resp.status_code == 200, scheduler_resp.text
    assert scheduler_resp.json()["created_alerts"] >= 1
    assert scheduler_resp.json()["escalated_instances"] >= 1

    my_alerts_resp = client.get("/api/v1/alerts/my", headers=manager_headers)
    assert my_alerts_resp.status_code == 200, my_alerts_resp.text
    assert any(alert["alert_type"] == "SLA Overdue" for alert in my_alerts_resp.json())

    dashboard_resp = client.get("/api/v1/dashboard/summary", headers=manager_headers)
    assert dashboard_resp.status_code == 200, dashboard_resp.text
    assert dashboard_resp.json()["open_alerts"] >= 1
    assert dashboard_resp.json()["escalated_workflow_instances"] >= 1
