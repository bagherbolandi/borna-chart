from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class GoodsReceiptCreate(BaseModel):
    purchase_order_id: int
    receipt_date: date
    warehouse_code: str
    supplier_delivery_ref: str | None = None
    received_qty: float = Field(gt=0)
    actor: str
    actor_role: str


class GoodsReceiptRead(ORMModel):
    id: int
    code: str
    purchase_order_id: int
    receipt_date: str
    warehouse_code: str
    supplier_delivery_ref: str | None
    received_qty: float
    status: str
    workflow_instance_id: int | None
