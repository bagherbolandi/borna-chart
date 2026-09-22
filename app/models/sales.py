from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import AuditMixin


class Product(AuditMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    family: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uom: Mapped[str] = mapped_column(String(20), nullable=False)
    standard_cost: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    approved_min_price: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    pricing_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)


class PriceList(AuditMixin, Base):
    __tablename__ = "price_lists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    pricing_method: Mapped[str] = mapped_column(String(50), nullable=False)
    cost_basis: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    target_margin_pct: Mapped[float] = mapped_column(Numeric(9, 4), default=0, nullable=False)
    logistics_cost: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    financial_cost: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    risk_cost: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    proposed_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    approved_min_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    valid_from: Mapped[str] = mapped_column(String(20), nullable=False)
    valid_to: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pricing_review", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class SalesOrder(AuditMixin, Base):
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("price_lists.id"), nullable=False)
    sales_owner: Mapped[str] = mapped_column(String(100), nullable=False)
    order_date: Mapped[str] = mapped_column(String(20), nullable=False)
    requested_delivery_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    qty: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    credit_check_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    pricing_status: Mapped[str] = mapped_column(String(30), default="approved", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="credit_check", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class SalesDelivery(AuditMixin, Base):
    __tablename__ = "sales_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), nullable=False)
    planned_date: Mapped[str] = mapped_column(String(20), nullable=False)
    released_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    delivered_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    warehouse_code: Mapped[str] = mapped_column(String(50), nullable=False)
    dispatch_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    planned_qty: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    delivered_qty: Mapped[float] = mapped_column(Numeric(18, 6), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="planning_allocation", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class SalesInvoice(AuditMixin, Base):
    __tablename__ = "sales_invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), nullable=False)
    sales_delivery_id: Mapped[int] = mapped_column(ForeignKey("sales_deliveries.id"), nullable=False)
    invoice_no: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[str] = mapped_column(String(20), nullable=False)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    collected_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    collection_status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="collection_open", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)


class CollectionReceipt(AuditMixin, Base):
    __tablename__ = "collection_receipts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sales_invoice_id: Mapped[int] = mapped_column(ForeignKey("sales_invoices.id"), nullable=False)
    receipt_date: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    collector: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="collected", nullable=False)
    workflow_instance_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_instances.id"), nullable=True)
