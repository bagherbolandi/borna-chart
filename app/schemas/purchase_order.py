from datetime import date

from pydantic import BaseModel

from app.schemas.common import ORMModel


class PurchaseOrderCreate(BaseModel):
    rfq_id: int
    selected_quotation_id: int
    order_date: date
    delivery_date: date | None = None
    emergency_flag: bool = False
    actor: str
    actor_role: str
    exception_approved: bool = False
    note: str | None = None


class PurchaseOrderRead(ORMModel):
    id: int
    code: str
    purchase_request_id: int
    rfq_id: int
    selected_quotation_id: int
    supplier_id: int
    order_date: str
    delivery_date: str | None
    currency: str
    payment_terms: str | None
    total_amount: float
    price_variance_pct: float | None
    emergency_flag: bool
    status: str
    workflow_instance_id: int | None
