from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ProductCreate(BaseModel):
    code: str
    name: str
    family: str | None = None
    uom: str
    standard_cost: float = Field(default=0, ge=0)
    approved_min_price: float = Field(default=0, ge=0)
    pricing_method: str | None = None
    status: str = "active"
    created_by: str | None = None


class ProductRead(ORMModel):
    id: int
    code: str
    name: str
    family: str | None = None
    uom: str
    standard_cost: float
    approved_min_price: float
    pricing_method: str | None = None
    status: str
