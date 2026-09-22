from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import AuditMixin


class PurchaseRequest(AuditMixin, Base):
    __tablename__ = "purchase_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    requester: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    need_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    cost_center_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    budget_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    total_estimated_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="IRR", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class PurchaseRequestLine(AuditMixin, Base):
    __tablename__ = "purchase_request_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    purchase_request_id: Mapped[int] = mapped_column(ForeignKey("purchase_requests.id"), nullable=False)
    line_no: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    material_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qty: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    uom: Mapped[str] = mapped_column(String(20), nullable=False)
    estimated_unit_price: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    cost_center_code: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)


class RFQ(AuditMixin, Base):
    __tablename__ = "rfqs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    purchase_request_id: Mapped[int] = mapped_column(ForeignKey("purchase_requests.id"), nullable=False)
    issue_date: Mapped[str] = mapped_column(String(20), nullable=False)
    close_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    minimum_quote_count: Mapped[int] = mapped_column(default=3, nullable=False)
    buyer: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="rfq_created", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class SupplierQuotation(AuditMixin, Base):
    __tablename__ = "supplier_quotations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"), nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    quote_no: Mapped[str] = mapped_column(String(100), nullable=False)
    quote_date: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    validity_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    delivery_days: Mapped[int | None] = mapped_column(nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    price_variance_pct: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    commercial_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    technical_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_selected: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="received", nullable=False)


class PurchaseOrder(AuditMixin, Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    purchase_request_id: Mapped[int] = mapped_column(ForeignKey("purchase_requests.id"), nullable=False)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"), nullable=False)
    selected_quotation_id: Mapped[int] = mapped_column(ForeignKey("supplier_quotations.id"), nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    order_date: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    price_variance_pct: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    emergency_flag: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="po_issued", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class GoodsReceipt(AuditMixin, Base):
    __tablename__ = "goods_receipts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    receipt_date: Mapped[str] = mapped_column(String(20), nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_delivery_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    received_qty: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="received", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class QualityInspection(AuditMixin, Base):
    __tablename__ = "quality_inspections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    goods_receipt_id: Mapped[int] = mapped_column(ForeignKey("goods_receipts.id"), nullable=False)
    inspection_date: Mapped[str] = mapped_column(String(20), nullable=False)
    inspector: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    accepted_qty: Mapped[float] = mapped_column(Numeric(18, 6), default=0, nullable=False)
    rejected_qty: Mapped[float] = mapped_column(Numeric(18, 6), default=0, nullable=False)
    defect_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="qc_pending", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class SupplierInvoice(AuditMixin, Base):
    __tablename__ = "supplier_invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    goods_receipt_id: Mapped[int] = mapped_column(ForeignKey("goods_receipts.id"), nullable=False)
    invoice_no: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[str] = mapped_column(String(20), nullable=False)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    match_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class Payment(AuditMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    supplier_invoice_id: Mapped[int] = mapped_column(ForeignKey("supplier_invoices.id"), nullable=False)
    payment_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="created", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)
