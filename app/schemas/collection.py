from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CollectionReceiptCreate(BaseModel):
    sales_invoice_id: int
    receipt_date: date
    amount: float = Field(gt=0)
    currency: str = "IRR"
    payment_method: str | None = None
    bank_reference: str | None = None
    actor: str
    actor_role: str


class CollectionReceiptRead(ORMModel):
    id: int
    code: str
    sales_invoice_id: int
    receipt_date: str
    amount: float
    currency: str
    payment_method: str | None
    bank_reference: str | None
    collector: str
    status: str
    workflow_instance_id: int | None
