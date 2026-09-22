from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CustomerCreate(BaseModel):
    code: str
    name: str
    payment_terms: str | None = None
    credit_limit: float = Field(default=0, ge=0)
    credit_status: str = "open"
    created_by: str | None = None


class CustomerRead(ORMModel):
    id: int
    code: str
    name: str
    payment_terms: str | None = None
    credit_limit: float
    credit_status: str
