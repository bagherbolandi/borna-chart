from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PaymentCreate(BaseModel):
    supplier_invoice_id: int
    payment_date: date | None = None
    amount: float = Field(gt=0)
    currency: str = "IRR"
    payment_method: str | None = None
    bank_reference: str | None = None
    actor: str
    actor_role: str = "AP Accountant"


class PaymentAction(BaseModel):
    actor: str
    actor_role: str
    note: str | None = None


class PaymentRead(ORMModel):
    id: int
    code: str
    supplier_invoice_id: int
    payment_date: str | None
    amount: float
    currency: str
    payment_method: str | None
    bank_reference: str | None
    status: str
    workflow_instance_id: int | None
