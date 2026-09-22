from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SupplierInvoiceCreate(BaseModel):
    supplier_id: int
    purchase_order_id: int
    goods_receipt_id: int
    invoice_no: str
    invoice_date: date
    due_date: date | None = None
    currency: str = "IRR"
    total_amount: float = Field(gt=0)
    actor: str
    actor_role: str = "AP Accountant"


class SupplierInvoiceMatch(BaseModel):
    actor: str
    actor_role: str
    note: str | None = None


class SupplierInvoiceRead(ORMModel):
    id: int
    code: str
    supplier_id: int
    purchase_order_id: int
    goods_receipt_id: int
    invoice_no: str
    invoice_date: str
    due_date: str | None
    currency: str
    total_amount: float
    match_status: str
    status: str
    workflow_instance_id: int | None
