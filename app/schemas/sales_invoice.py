from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SalesInvoiceCreate(BaseModel):
    sales_order_id: int
    sales_delivery_id: int
    invoice_no: str
    invoice_date: date
    due_date: date | None = None
    currency: str = "IRR"
    total_amount: float = Field(gt=0)
    actor: str
    actor_role: str


class SalesInvoiceRead(ORMModel):
    id: int
    code: str
    sales_order_id: int
    sales_delivery_id: int
    invoice_no: str
    invoice_date: str
    due_date: str | None
    currency: str
    total_amount: float
    collected_amount: float
    collection_status: str
    status: str
    workflow_instance_id: int | None
