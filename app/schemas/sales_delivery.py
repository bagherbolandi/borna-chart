from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SalesDeliveryCreate(BaseModel):
    sales_order_id: int
    planned_date: date
    warehouse_code: str
    planned_qty: float = Field(gt=0)
    actor: str
    actor_role: str


class SalesDeliveryRelease(BaseModel):
    actor: str
    actor_role: str
    release_date: date | None = None
    note: str | None = None


class SalesDeliveryExecute(BaseModel):
    actor: str
    actor_role: str
    delivered_date: date
    delivered_qty: float = Field(gt=0)
    dispatch_reference: str | None = None
    note: str | None = None


class SalesDeliveryRead(ORMModel):
    id: int
    code: str
    sales_order_id: int
    planned_date: str
    released_date: str | None
    delivered_date: str | None
    warehouse_code: str
    dispatch_reference: str | None
    planned_qty: float
    delivered_qty: float
    status: str
    workflow_instance_id: int | None
