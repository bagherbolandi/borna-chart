from pydantic import BaseModel

from app.schemas.common import ORMModel


class SupplierCreate(BaseModel):
    code: str
    name: str
    approval_status: str = "pending"
    risk_level: str = "medium"
    payment_terms: str | None = None
    created_by: str | None = None


class SupplierRead(ORMModel):
    id: int
    code: str
    name: str
    approval_status: str
    risk_level: str
    payment_terms: str | None
