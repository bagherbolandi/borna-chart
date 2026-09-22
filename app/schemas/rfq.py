from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class RFQCreate(BaseModel):
    purchase_request_id: int
    issue_date: date
    close_date: date | None = None
    minimum_quote_count: int = Field(default=3, ge=1)
    buyer: str
    created_by: str | None = None


class RFQRead(ORMModel):
    id: int
    code: str
    purchase_request_id: int
    issue_date: str
    close_date: str | None
    minimum_quote_count: int
    buyer: str
    status: str
    workflow_instance_id: int | None


class QuotationCreate(BaseModel):
    supplier_id: int
    quote_no: str
    quote_date: date
    currency: str = "IRR"
    validity_date: date | None = None
    delivery_days: int | None = None
    payment_terms: str | None = None
    total_amount: float = Field(gt=0)
    price_variance_pct: float | None = None
    commercial_score: float | None = None
    technical_score: float | None = None
    created_by: str | None = None


class QuotationRead(ORMModel):
    id: int
    rfq_id: int
    supplier_id: int
    quote_no: str
    quote_date: str
    currency: str
    validity_date: str | None
    delivery_days: int | None
    payment_terms: str | None
    total_amount: float
    price_variance_pct: float | None
    commercial_score: float | None
    technical_score: float | None
    is_selected: bool
    status: str


class CommercialEvaluationAction(BaseModel):
    actor: str
    actor_role: str
    selected_quotation_id: int
    note: str | None = None


class RFQDetail(RFQRead):
    current_state: str | None = None
    current_owner: str | None = None
    current_role: str | None = None
    quotations: list[QuotationRead] = Field(default_factory=list)
