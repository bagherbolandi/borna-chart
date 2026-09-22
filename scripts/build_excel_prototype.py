from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_DIR = ROOT / "prototype"
CSV_DIR = PROTOTYPE_DIR / "csv"
CONFIG_DIR = ROOT / "config"
WORKFLOWS_DIR = CONFIG_DIR / "workflows"
RULES_DIR = CONFIG_DIR / "rules"
SECURITY_DIR = CONFIG_DIR / "security"

SHEET_SPECS = [
    {
        "name": "Dashboard",
        "headers": [
            "widget_id", "widget_name", "process", "metric", "value", "unit",
            "status", "owner_role", "last_refresh_at", "notes"
        ],
        "rows": [
            ["W-001", "Open PR", "Procurement", "count", "", "", "active", "Procurement Manager", "", "KPI placeholder"],
            ["W-002", "Overdue Receivables", "Finance", "amount", "", "IRR", "active", "Finance Manager", "", "KPI placeholder"],
        ],
    },
    {
        "name": "Workflow",
        "headers": [
            "workflow_id", "process", "object_type", "object_code", "current_state", "next_state",
            "current_owner", "current_role", "due_at", "overdue_days", "escalation_level",
            "exception_flag", "financial_impact", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Users",
        "headers": [
            "user_id", "username", "full_name", "department", "email", "mobile",
            "status", "default_role", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Roles",
        "headers": [
            "role_id", "role_code", "role_name", "process_scope", "department_scope",
            "approval_limit_code", "status", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Suppliers",
        "headers": [
            "supplier_id", "supplier_code", "supplier_name", "category", "approval_status",
            "payment_terms", "currency", "risk_level", "quality_score", "delivery_score",
            "performance_score", "status", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Customers",
        "headers": [
            "customer_id", "customer_code", "customer_name", "payment_terms", "credit_limit",
            "credit_status", "market_segment", "risk_level", "status", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Materials",
        "headers": [
            "material_id", "material_code", "material_name", "uom", "material_type",
            "category", "specification", "status", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Products",
        "headers": [
            "product_id", "product_code", "product_name", "family", "uom",
            "standard_cost", "approved_min_price", "pricing_method", "status",
            "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "BOM",
        "headers": [
            "bom_id", "product_code", "revision_no", "component_code", "operation_no",
            "qty", "scrap_factor", "effective_from", "effective_to", "status",
            "approved_by", "approved_at"
        ],
        "rows": [],
    },
    {
        "name": "PR",
        "headers": [
            "pr_id", "pr_code", "requester", "department", "need_date", "request_type",
            "budget_status", "priority", "total_estimated_amount", "currency", "reason",
            "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "RFQ",
        "headers": [
            "rfq_id", "rfq_code", "pr_code", "issue_date", "close_date", "minimum_quote_count",
            "buyer", "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Quotations",
        "headers": [
            "quotation_id", "rfq_code", "supplier_code", "quote_no", "quote_date", "currency",
            "validity_date", "delivery_days", "payment_terms", "total_amount", "price_variance_pct",
            "commercial_score", "technical_score", "selected_flag", "status", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Purchase Orders",
        "headers": [
            "po_id", "po_code", "pr_code", "rfq_code", "supplier_code", "order_date",
            "delivery_date", "currency", "payment_terms", "total_amount", "price_variance_pct",
            "emergency_flag", "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Receipts",
        "headers": [
            "grn_id", "grn_code", "po_code", "receipt_date", "warehouse_code", "supplier_delivery_ref",
            "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "QC",
        "headers": [
            "qc_id", "qc_code", "grn_code", "inspection_date", "inspector", "result",
            "accepted_qty", "rejected_qty", "defect_code", "corrective_action", "status",
            "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Costing",
        "headers": [
            "cost_sheet_id", "cost_sheet_code", "product_code", "production_order_code", "costing_type",
            "material_cost", "labor_cost", "machine_cost", "energy_cost", "overhead_cost",
            "scrap_cost", "rework_cost", "packaging_cost", "internal_logistics_cost",
            "total_cost", "standard_cost", "actual_cost", "estimated_cost", "variance_amount",
            "variance_pct", "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Pricing",
        "headers": [
            "price_list_id", "price_list_code", "product_code", "customer_code", "pricing_method",
            "cost_basis", "target_margin_pct", "logistics_cost", "financial_cost", "risk_cost",
            "proposed_price", "approved_min_price", "valid_from", "valid_to", "status",
            "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Sales Orders",
        "headers": [
            "so_id", "so_code", "customer_code", "order_date", "requested_delivery_date",
            "payment_terms", "currency", "total_amount", "credit_check_status", "pricing_status",
            "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Delivery",
        "headers": [
            "delivery_id", "delivery_code", "so_code", "delivery_date", "warehouse_code",
            "carrier_name", "proof_of_delivery_ref", "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Invoices",
        "headers": [
            "invoice_id", "invoice_code", "invoice_type", "counterparty_code", "reference_code",
            "invoice_no", "invoice_date", "due_date", "currency", "total_amount", "match_status",
            "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Payments",
        "headers": [
            "payment_id", "payment_code", "invoice_code", "payment_date", "amount", "currency",
            "payment_method", "bank_reference", "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Projects",
        "headers": [
            "project_id", "project_code", "project_name", "project_type", "sponsor", "project_manager",
            "baseline_budget", "actual_cost", "baseline_start_date", "baseline_end_date",
            "actual_start_date", "actual_end_date", "schedule_variance_days", "budget_variance_amount",
            "status", "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Approvals",
        "headers": [
            "approval_id", "object_type", "object_code", "approval_stage", "approver", "approver_role",
            "decision", "decision_note", "decided_at", "delegated_from", "created_at"
        ],
        "rows": [],
    },
    {
        "name": "Exceptions",
        "headers": [
            "exception_id", "exception_code", "related_object_type", "related_object_code",
            "exception_type", "justification", "approver", "approved_at", "status",
            "workflow_id", "created_at", "modified_at"
        ],
        "rows": [],
    },
    {
        "name": "Alerts",
        "headers": [
            "alert_id", "alert_code", "related_object_type", "related_object_code", "alert_type",
            "severity", "owner", "generated_at", "due_at", "financial_impact", "status", "resolution_note"
        ],
        "rows": [],
    },
    {
        "name": "Audit Trail",
        "headers": [
            "audit_id", "event_time", "user", "entity_name", "entity_code", "action",
            "field_name", "old_value", "new_value", "reason", "authorized_by", "session_id", "ip_address"
        ],
        "rows": [],
    },
    {
        "name": "KPI",
        "headers": [
            "kpi_id", "kpi_code", "kpi_name", "formula", "owner_role", "target_value",
            "as_of_date", "dimension_1", "dimension_2", "metric_value", "status"
        ],
        "rows": [],
    },
    {
        "name": "Settings",
        "headers": [
            "setting_group", "setting_key", "setting_value", "value_type", "effective_from",
            "effective_to", "status", "notes"
        ],
        "rows": [
            ["SLA", "PR_REVIEW_DAYS", "1", "integer", "2026-01-01", "", "active", "Configurable"],
            ["DOA", "PURCHASE_LEVEL_1", "Department Manager", "string", "2026-01-01", "", "active", "Configurable"],
            ["RULE", "MIN_RFQ_QUOTES", "3", "integer", "2026-01-01", "", "active", "Configurable"],
        ],
    },
]

WORKFLOW_CONFIGS = {
    "procurement.json": {
        "process": "procurement",
        "object_type": "procurement_case",
        "states": [
            {"code": "draft", "name": "Draft", "initial": True},
            {"code": "submitted", "name": "Submitted"},
            {"code": "under_review", "name": "Under Review"},
            {"code": "approved", "name": "Approved"},
            {"code": "rfq_created", "name": "RFQ Created"},
            {"code": "quotation_received", "name": "Quotation Received"},
            {"code": "commercial_evaluated", "name": "Commercial Evaluated"},
            {"code": "technically_approved", "name": "Technically Approved"},
            {"code": "price_approved", "name": "Price Approved"},
            {"code": "po_issued", "name": "PO Issued"},
            {"code": "waiting_delivery", "name": "Waiting Delivery"},
            {"code": "received", "name": "Received"},
            {"code": "qc_pending", "name": "QC Pending"},
            {"code": "accepted", "name": "Accepted"},
            {"code": "rejected", "name": "Rejected"},
            {"code": "inventory_released", "name": "Inventory Released"},
            {"code": "invoice_matched", "name": "Invoice Matched"},
            {"code": "payment_approved", "name": "Payment Approved"},
            {"code": "paid", "name": "Paid"},
            {"code": "closed", "name": "Closed", "final": True},
        ],
        "transitions": [
            {"from": "draft", "to": "submitted", "action": "submit", "roles": ["Requester"], "rules": ["PR-001"]},
            {"from": "submitted", "to": "under_review", "action": "route_review", "roles": ["System", "Department Manager"], "rules": ["PR-002"]},
            {"from": "under_review", "to": "approved", "action": "approve", "roles": ["Department Manager", "Finance Manager"], "rules": ["SOD-001"]},
            {"from": "approved", "to": "rfq_created", "action": "create_rfq", "roles": ["Procurement Officer"], "rules": ["RFQ-001"]},
            {"from": "rfq_created", "to": "quotation_received", "action": "record_quotes", "roles": ["Procurement Officer"], "rules": ["RFQ-002"]},
            {"from": "quotation_received", "to": "commercial_evaluated", "action": "commercial_eval", "roles": ["Procurement Officer"], "rules": ["QUO-001"]},
            {"from": "commercial_evaluated", "to": "technically_approved", "action": "technical_eval", "roles": ["Technical Evaluator"], "rules": []},
            {"from": "technically_approved", "to": "price_approved", "action": "approve_price", "roles": ["Procurement Manager", "Finance Manager"], "rules": ["PO-002"]},
            {"from": "price_approved", "to": "po_issued", "action": "issue_po", "roles": ["Procurement Officer"], "rules": ["PO-001", "SUP-001"]},
            {"from": "po_issued", "to": "waiting_delivery", "action": "release_supplier", "roles": ["System"], "rules": []},
            {"from": "waiting_delivery", "to": "received", "action": "record_receipt", "roles": ["Warehouse Receiver"], "rules": ["GRN-001"]},
            {"from": "received", "to": "qc_pending", "action": "send_to_qc", "roles": ["System", "Warehouse Receiver"], "rules": []},
            {"from": "qc_pending", "to": "accepted", "action": "accept_qc", "roles": ["QC Inspector"], "rules": ["QC-001"]},
            {"from": "qc_pending", "to": "rejected", "action": "reject_qc", "roles": ["QC Inspector"], "rules": ["QC-001"]},
            {"from": "accepted", "to": "inventory_released", "action": "release_inventory", "roles": ["Warehouse Receiver"], "rules": ["QC-001"]},
            {"from": "inventory_released", "to": "invoice_matched", "action": "match_invoice", "roles": ["AP Accountant"], "rules": ["INV-001"]},
            {"from": "invoice_matched", "to": "payment_approved", "action": "approve_payment", "roles": ["Finance Manager"], "rules": ["PAY-001"]},
            {"from": "payment_approved", "to": "paid", "action": "execute_payment", "roles": ["Treasury Officer"], "rules": ["PAY-001"]},
            {"from": "paid", "to": "closed", "action": "close_case", "roles": ["System", "Procurement Manager"], "rules": []},
        ],
    },
    "sales.json": {
        "process": "sales",
        "object_type": "sales_case",
        "states": [
            {"code": "draft_inquiry", "name": "Draft Inquiry", "initial": True},
            {"code": "quoted", "name": "Quoted"},
            {"code": "pricing_review", "name": "Pricing Review"},
            {"code": "price_approved", "name": "Price Approved"},
            {"code": "credit_check", "name": "Credit Check"},
            {"code": "sales_order_confirmed", "name": "Sales Order Confirmed"},
            {"code": "planning_allocation", "name": "Planning/Allocation"},
            {"code": "ready_to_deliver", "name": "Ready to Deliver"},
            {"code": "delivered", "name": "Delivered"},
            {"code": "invoiced", "name": "Invoiced"},
            {"code": "collection_open", "name": "Collection Open"},
            {"code": "collected", "name": "Collected"},
            {"code": "profitability_reviewed", "name": "Profitability Reviewed"},
            {"code": "closed", "name": "Closed", "final": True},
        ],
        "transitions": [
            {"from": "draft_inquiry", "to": "quoted", "action": "issue_quote", "roles": ["Sales Officer"], "rules": []},
            {"from": "quoted", "to": "pricing_review", "action": "send_pricing_review", "roles": ["Sales Officer"], "rules": ["PRC-001"]},
            {"from": "pricing_review", "to": "price_approved", "action": "approve_price", "roles": ["Pricing Analyst", "Sales Manager", "Finance Manager"], "rules": ["PRC-002"]},
            {"from": "price_approved", "to": "credit_check", "action": "run_credit_check", "roles": ["System", "Credit Controller"], "rules": ["SAL-001"]},
            {"from": "credit_check", "to": "sales_order_confirmed", "action": "confirm_so", "roles": ["Sales Manager"], "rules": ["SAL-001"]},
            {"from": "sales_order_confirmed", "to": "planning_allocation", "action": "allocate_supply", "roles": ["Planning Officer"], "rules": []},
            {"from": "planning_allocation", "to": "ready_to_deliver", "action": "release_delivery", "roles": ["Planning Officer", "Warehouse Receiver"], "rules": []},
            {"from": "ready_to_deliver", "to": "delivered", "action": "deliver", "roles": ["Logistics Officer"], "rules": ["DEL-001"]},
            {"from": "delivered", "to": "invoiced", "action": "invoice", "roles": ["AR Accountant"], "rules": ["DEL-001"]},
            {"from": "invoiced", "to": "collection_open", "action": "open_collection", "roles": ["System"], "rules": []},
            {"from": "collection_open", "to": "collected", "action": "allocate_receipt", "roles": ["Collections Officer"], "rules": []},
            {"from": "collected", "to": "profitability_reviewed", "action": "analyze_margin", "roles": ["Pricing Analyst", "Finance Manager"], "rules": []},
            {"from": "profitability_reviewed", "to": "closed", "action": "close_case", "roles": ["System", "Sales Manager"], "rules": []},
        ],
    },
    "project.json": {
        "process": "project",
        "object_type": "project_case",
        "states": [
            {"code": "idea_logged", "name": "Idea Logged", "initial": True},
            {"code": "screening", "name": "Screening"},
            {"code": "feasibility", "name": "Feasibility"},
            {"code": "business_case_prepared", "name": "Business Case Prepared"},
            {"code": "investment_approved", "name": "Investment Approved"},
            {"code": "project_initiated", "name": "Project Initiated"},
            {"code": "execution", "name": "Execution"},
            {"code": "commissioning", "name": "Commissioning"},
            {"code": "launch", "name": "Launch"},
            {"code": "post_implementation_review", "name": "Post Implementation Review"},
            {"code": "closed", "name": "Closed", "final": True},
        ],
        "transitions": [
            {"from": "idea_logged", "to": "screening", "action": "screen", "roles": ["PMO"], "rules": []},
            {"from": "screening", "to": "feasibility", "action": "start_feasibility", "roles": ["Engineering Manager"], "rules": []},
            {"from": "feasibility", "to": "business_case_prepared", "action": "prepare_business_case", "roles": ["Finance Manager", "Project Manager"], "rules": []},
            {"from": "business_case_prepared", "to": "investment_approved", "action": "approve_investment", "roles": ["Investment Committee"], "rules": ["PROJ-001"]},
            {"from": "investment_approved", "to": "project_initiated", "action": "initiate_project", "roles": ["Project Manager"], "rules": ["PROJ-001"]},
            {"from": "project_initiated", "to": "execution", "action": "execute", "roles": ["Project Manager"], "rules": []},
            {"from": "execution", "to": "commissioning", "action": "commission", "roles": ["Operations Manager"], "rules": []},
            {"from": "commissioning", "to": "launch", "action": "launch", "roles": ["Operations Manager"], "rules": []},
            {"from": "launch", "to": "post_implementation_review", "action": "pir", "roles": ["Internal Auditor", "PMO"], "rules": []},
            {"from": "post_implementation_review", "to": "closed", "action": "close_project", "roles": ["Sponsor", "PMO"], "rules": []},
        ],
    },
    "change_request.json": {
        "process": "change_request",
        "object_type": "change_request",
        "states": [
            {"code": "draft", "name": "Draft", "initial": True},
            {"code": "submitted", "name": "Submitted"},
            {"code": "impact_analysis", "name": "Impact Analysis"},
            {"code": "approval", "name": "Approval"},
            {"code": "implementation", "name": "Implementation"},
            {"code": "verification", "name": "Verification"},
            {"code": "closed", "name": "Closed", "final": True},
            {"code": "rejected", "name": "Rejected", "final": True},
        ],
        "transitions": [
            {"from": "draft", "to": "submitted", "action": "submit", "roles": ["Any Authorized User"], "rules": []},
            {"from": "submitted", "to": "impact_analysis", "action": "analyze", "roles": ["Process Owner", "Finance Manager", "Engineering Manager"], "rules": []},
            {"from": "impact_analysis", "to": "approval", "action": "route_approval", "roles": ["System"], "rules": []},
            {"from": "approval", "to": "implementation", "action": "approve", "roles": ["Relevant Approver"], "rules": []},
            {"from": "implementation", "to": "verification", "action": "verify", "roles": ["Independent Verifier"], "rules": []},
            {"from": "verification", "to": "closed", "action": "close", "roles": ["Process Owner"], "rules": []},
            {"from": "approval", "to": "rejected", "action": "reject", "roles": ["Relevant Approver"], "rules": []},
        ],
    },
}

BUSINESS_RULES = {
    "version": "1.0",
    "rules": [
        {"code": "PR-001", "process": "procurement", "object_type": "PR", "event": "submit", "severity": "block", "description": "PR without cost center and need reason cannot be submitted."},
        {"code": "PR-002", "process": "procurement", "object_type": "PR", "event": "route_review", "severity": "block", "description": "PR above budget cannot proceed without approved exception."},
        {"code": "RFQ-001", "process": "procurement", "object_type": "RFQ", "event": "create", "severity": "block", "description": "RFQ is prohibited before PR approval."},
        {"code": "RFQ-002", "process": "procurement", "object_type": "RFQ", "event": "submit", "severity": "block", "description": "Minimum number of quotations must comply with policy or approved exception."},
        {"code": "QUO-001", "process": "procurement", "object_type": "QuotationEvaluation", "event": "approve", "severity": "block", "description": "Commercial comparison is mandatory before PO issue."},
        {"code": "SUP-001", "process": "procurement", "object_type": "PO", "event": "issue", "severity": "block", "description": "Supplier must be in approved status to be used on PO."},
        {"code": "SUP-002", "process": "procurement", "object_type": "PO", "event": "issue", "severity": "escalate", "description": "High-risk supplier requires additional approval."},
        {"code": "PO-001", "process": "procurement", "object_type": "PO", "event": "issue", "severity": "block", "description": "PO without evaluation and valid approval is not allowed."},
        {"code": "PO-002", "process": "procurement", "object_type": "PO", "event": "approve_price", "severity": "escalate", "description": "Purchase price variance above threshold requires escalation."},
        {"code": "GRN-001", "process": "procurement", "object_type": "GRN", "event": "create", "severity": "block", "description": "Receipt without valid PO is not allowed unless approved exception exists."},
        {"code": "QC-001", "process": "quality", "object_type": "QC", "event": "finalize", "severity": "block", "description": "Rejected quantity cannot be released to usable inventory."},
        {"code": "INV-001", "process": "finance", "object_type": "SupplierInvoice", "event": "match", "severity": "block", "description": "Supplier invoice requires valid PO/GRN match."},
        {"code": "PAY-001", "process": "finance", "object_type": "Payment", "event": "approve", "severity": "block", "description": "Payment without successful three-way match is prohibited."},
        {"code": "CST-001", "process": "costing", "object_type": "CostSheet", "event": "approve", "severity": "block", "description": "Cost sheet without approved absorption rates cannot be approved."},
        {"code": "PRC-001", "process": "pricing", "object_type": "PriceProposal", "event": "submit", "severity": "block", "description": "Final product pricing requires approved cost basis."},
        {"code": "PRC-002", "process": "pricing", "object_type": "SalesOrder", "event": "approve", "severity": "escalate", "description": "Sales price below approved minimum triggers approval escalation."},
        {"code": "SAL-001", "process": "sales", "object_type": "SalesOrder", "event": "confirm", "severity": "block", "description": "Customer orders above credit limit are blocked or placed on hold."},
        {"code": "DEL-001", "process": "sales", "object_type": "Delivery", "event": "create", "severity": "block", "description": "Delivery without valid sales order is not allowed."},
        {"code": "BOM-001", "process": "engineering", "object_type": "BOM", "event": "change", "severity": "block", "description": "BOM change without approved change request is prohibited."},
        {"code": "PROJ-001", "process": "project", "object_type": "Project", "event": "execute", "severity": "block", "description": "Project execution cannot start before investment approval."},
        {"code": "PROJ-002", "process": "project", "object_type": "Project", "event": "monitor", "severity": "escalate", "description": "Budget overrun above threshold must be escalated."},
        {"code": "AUD-001", "process": "audit", "object_type": "SensitiveChange", "event": "update", "severity": "alert", "description": "Sensitive changes to price, terms, or limits must be logged and alerted."},
        {"code": "SOD-001", "process": "security", "object_type": "Approval", "event": "approve", "severity": "block", "description": "Requester and final approver cannot be the same person for the same object."}
    ]
}

DOA_MATRIX = {
    "purchase": [
        {"level": 1, "max_amount": 100000000, "approvers": ["Department Manager"]},
        {"level": 2, "max_amount": 500000000, "approvers": ["Department Manager", "Finance Manager"]},
        {"level": 3, "max_amount": 2000000000, "approvers": ["COO", "CFO"]},
        {"level": 4, "max_amount": None, "approvers": ["CEO", "Committee"]}
    ],
    "sales_below_floor": [
        {"level": 1, "threshold_pct": 2, "approvers": ["Sales Manager"]},
        {"level": 2, "threshold_pct": 5, "approvers": ["Sales Manager", "Finance Manager"]},
        {"level": 3, "threshold_pct": 10, "approvers": ["CEO"]}
    ],
    "project_capex": [
        {"level": 1, "max_amount": 500000000, "approvers": ["Project Sponsor"]},
        {"level": 2, "max_amount": 2000000000, "approvers": ["PMO", "Finance Manager"]},
        {"level": 3, "max_amount": None, "approvers": ["Investment Committee"]}
    ]
}

SOD_MATRIX = {
    "prohibited_pairs": [
        {"actor_role": "Requester", "restricted_role": "Final Approver", "scope": "same_document"},
        {"actor_role": "Buyer", "restricted_role": "Goods Receiver", "scope": "same_po"},
        {"actor_role": "Goods Receiver", "restricted_role": "QC Approver", "scope": "same_receipt"},
        {"actor_role": "AP Matcher", "restricted_role": "Payment Executor", "scope": "same_invoice"},
        {"actor_role": "Sales Creator", "restricted_role": "Discount Final Approver", "scope": "same_order"},
        {"actor_role": "Project Requester", "restricted_role": "Budget Final Approver", "scope": "same_project"},
        {"actor_role": "Master Data Admin", "restricted_role": "Audit Log Admin", "scope": "platform"}
    ]
}

SLA_PROFILES = {
    "profiles": [
        {"code": "PR_REVIEW", "process": "procurement", "stage": "under_review", "duration": 1, "unit": "business_day", "escalation_profile": "APPROVAL_DELAY"},
        {"code": "SUPPLIER_EVAL", "process": "procurement", "stage": "commercial_evaluated", "duration": 2, "unit": "business_day", "escalation_profile": "APPROVAL_DELAY"},
        {"code": "QUOTE_ANALYSIS", "process": "procurement", "stage": "quotation_received", "duration": 2, "unit": "business_day", "escalation_profile": "APPROVAL_DELAY"},
        {"code": "PO_ISSUE", "process": "procurement", "stage": "price_approved", "duration": 1, "unit": "business_day", "escalation_profile": "APPROVAL_DELAY"},
        {"code": "QC_STANDARD", "process": "quality", "stage": "qc_pending", "duration": 1, "unit": "business_day", "escalation_profile": "APPROVAL_DELAY"},
        {"code": "INVOICE_MATCH", "process": "finance", "stage": "invoice_matched", "duration": 1, "unit": "business_day", "escalation_profile": "APPROVAL_DELAY"},
        {"code": "PROJECT_MILESTONE", "process": "project", "stage": "execution", "duration": 5, "unit": "business_day", "escalation_profile": "PROJECT_DELAY"}
    ],
    "escalation_profiles": [
        {"code": "APPROVAL_DELAY", "levels": [
            {"level": 1, "after": "0h", "notify_roles": ["Owner"]},
            {"level": 2, "after": "8h", "notify_roles": ["Supervisor"]},
            {"level": 3, "after": "16h", "notify_roles": ["Process Owner"]},
            {"level": 4, "after": "24h", "notify_roles": ["Management"]}
        ]},
        {"code": "PROJECT_DELAY", "levels": [
            {"level": 1, "after": "0h", "notify_roles": ["Project Manager"]},
            {"level": 2, "after": "24h", "notify_roles": ["PMO"]},
            {"level": 3, "after": "48h", "notify_roles": ["Sponsor"]},
            {"level": 4, "after": "72h", "notify_roles": ["Committee"]}
        ]}
    ]
}


def ensure_dirs() -> None:
    for d in [PROTOTYPE_DIR, CSV_DIR, WORKFLOWS_DIR, RULES_DIR, SECURITY_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv_templates() -> None:
    for spec in SHEET_SPECS:
        csv_path = CSV_DIR / f"{spec['name'].replace(' ', '_')}.csv"
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(spec["headers"])
            for row in spec.get("rows", []):
                writer.writerow(row)


def col_letter(idx: int) -> str:
    letters = []
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters.append(chr(65 + rem))
    return "".join(reversed(letters))


def make_cell(ref: str, value: str, style: int = 0) -> str:
    safe = escape(str(value))
    return f'<c r="{ref}" t="inlineStr" s="{style}"><is><t>{safe}</t></is></c>'


def make_sheet_xml(headers: list[str], rows: list[list[str]]) -> str:
    all_rows = [headers] + rows
    row_xml = []
    for r_idx, row in enumerate(all_rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            ref = f"{col_letter(c_idx)}{r_idx}"
            style = 1 if r_idx == 1 else 0
            cells.append(make_cell(ref, value, style))
        row_xml.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    max_col = col_letter(len(headers))
    cols = []
    for c_idx, header in enumerate(headers, start=1):
        width = min(max(len(header) + 2, 12), 28)
        cols.append(f'<col min="{c_idx}" max="{c_idx}" width="{width}" customWidth="1"/>')
    cols_xml = "".join(cols)
    auto_filter_ref = f"A1:{max_col}1"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        '<selection pane="bottomLeft" activeCell="A2" sqref="A2"/>'
        '</sheetView></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<cols>{cols_xml}</cols>'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        f'<autoFilter ref="{auto_filter_ref}"/>'
        '</worksheet>'
    )


def make_content_types(sheet_count: int) -> str:
    overrides = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(1, sheet_count + 1):
        overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'{"".join(overrides)}'
        '</Types>'
    )


def make_root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>'
    )


def make_workbook_xml() -> str:
    sheets = []
    for idx, spec in enumerate(SHEET_SPECS, start=1):
        name = escape(spec["name"])
        sheets.append(f'<sheet name="{name}" sheetId="{idx}" r:id="rId{idx}"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<bookViews><workbookView xWindow="0" yWindow="0" windowWidth="24000" windowHeight="14000"/></bookViews>'
        f'<sheets>{"".join(sheets)}</sheets>'
        '</workbook>'
    )


def make_workbook_rels() -> str:
    rels = []
    for idx in range(1, len(SHEET_SPECS) + 1):
        rels.append(
            f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{len(SHEET_SPECS) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{"".join(rels)}'
        '</Relationships>'
    )


def make_styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2">'
        '<font><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/></font>'
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/><family val="2"/></font>'
        '</fonts>'
        '<fills count="3">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill>'
        '</fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )


def make_app_xml() -> str:
    titles = "".join(f'<vt:lpstr>{escape(spec["name"])}</vt:lpstr>' for spec in SHEET_SPECS)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<Application>Arena.ai Prototype Builder</Application>'
        f'<HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>{len(SHEET_SPECS)}</vt:i4></vt:variant></vt:vector></HeadingPairs>'
        f'<TitlesOfParts><vt:vector size="{len(SHEET_SPECS)}" baseType="lpstr">{titles}</vt:vector></TitlesOfParts>'
        '<Company>Arena.ai</Company>'
        '</Properties>'
    )


def make_core_xml() -> str:
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>Borna Process Control Prototype</dc:title>'
        '<dc:creator>Arena.ai</dc:creator>'
        '<cp:lastModifiedBy>Arena.ai</cp:lastModifiedBy>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        '</cp:coreProperties>'
    )


def build_xlsx() -> Path:
    output = PROTOTYPE_DIR / 'Borna_Process_Control_Prototype.xlsx'
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', make_content_types(len(SHEET_SPECS)))
        zf.writestr('_rels/.rels', make_root_rels())
        zf.writestr('xl/workbook.xml', make_workbook_xml())
        zf.writestr('xl/_rels/workbook.xml.rels', make_workbook_rels())
        zf.writestr('xl/styles.xml', make_styles_xml())
        zf.writestr('docProps/app.xml', make_app_xml())
        zf.writestr('docProps/core.xml', make_core_xml())
        for idx, spec in enumerate(SHEET_SPECS, start=1):
            xml = make_sheet_xml(spec['headers'], spec.get('rows', []))
            zf.writestr(f'xl/worksheets/sheet{idx}.xml', xml)
    return output


def write_configs() -> None:
    for filename, cfg in WORKFLOW_CONFIGS.items():
        write_json(WORKFLOWS_DIR / filename, cfg)
    write_json(RULES_DIR / 'business_rules.json', BUSINESS_RULES)
    write_json(SECURITY_DIR / 'doa_matrix.json', DOA_MATRIX)
    write_json(SECURITY_DIR / 'sod_matrix.json', SOD_MATRIX)
    write_json(CONFIG_DIR / 'sla_profiles.json', SLA_PROFILES)


def main() -> None:
    ensure_dirs()
    write_csv_templates()
    write_configs()
    output = build_xlsx()
    print(f'Generated: {output.relative_to(ROOT)}')
    print(f'CSV templates: {CSV_DIR.relative_to(ROOT)}')
    print(f'Config files: {CONFIG_DIR.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
