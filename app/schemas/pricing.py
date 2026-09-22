from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PriceListCreate(BaseModel):
    product_id: int
    customer_id: int | None = None
    pricing_method: str
    cost_basis: float = Field(gt=0)
    target_margin_pct: float = Field(default=0, ge=0)
    logistics_cost: float = Field(default=0, ge=0)
    financial_cost: float = Field(default=0, ge=0)
    risk_cost: float = Field(default=0, ge=0)
    proposed_price: float = Field(gt=0)
    approved_min_price: float = Field(gt=0)
    valid_from: date
    valid_to: date | None = None
    actor: str
    actor_role: str


class PriceApprovalAction(BaseModel):
    actor: str
    actor_role: str
    note: str | None = None


class PriceListRead(ORMModel):
    id: int
    code: str
    product_id: int
    customer_id: int | None
    pricing_method: str
    cost_basis: float
    target_margin_pct: float
    logistics_cost: float
    financial_cost: float
    risk_cost: float
    proposed_price: float
    approved_min_price: float
    valid_from: str
    valid_to: str | None
    status: str
    workflow_instance_id: int | None
