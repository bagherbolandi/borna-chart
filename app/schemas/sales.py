from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SalesOrderCreate(BaseModel):
    customer_id: int
    product_id: int
    price_list_id: int
    order_date: date
    requested_delivery_date: date | None = None
    qty: float = Field(gt=0)
    unit_price: float = Field(gt=0)
    actor: str
    actor_role: str


class SalesOrderAction(BaseModel):
    actor: str
    actor_role: str
    note: str | None = None


class SalesOrderRead(ORMModel):
    id: int
    code: str
    customer_id: int
    product_id: int
    price_list_id: int
    sales_owner: str
    order_date: str
    requested_delivery_date: str | None
    qty: float
    unit_price: float
    total_amount: float
    credit_check_status: str
    pricing_status: str
    status: str
    workflow_instance_id: int | None
