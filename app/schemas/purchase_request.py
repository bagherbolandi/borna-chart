from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PurchaseRequestLineCreate(BaseModel):
    line_no: int = Field(ge=1)
    description: str
    material_code: str | None = None
    qty: float = Field(gt=0)
    uom: str
    estimated_unit_price: float | None = Field(default=None, ge=0)
    cost_center_code: str


class PurchaseRequestCreate(BaseModel):
    requester: str
    department: str
    need_date: date | None = None
    reason: str
    cost_center_code: str | None = None
    budget_status: str = "within_budget"
    priority: str = "normal"
    total_estimated_amount: float = Field(default=0, ge=0)
    currency: str = "IRR"
    created_by: str | None = None
    lines: list[PurchaseRequestLineCreate] = Field(default_factory=list)


class PurchaseRequestSubmit(BaseModel):
    actor: str
    actor_role: str
    exception_approved: bool = False


class PurchaseRequestRead(ORMModel):
    id: int
    code: str
    requester: str
    department: str
    reason: str
    cost_center_code: str | None
    budget_status: str
    priority: str
    total_estimated_amount: float
    currency: str
    status: str
    workflow_instance_id: int | None


class PurchaseRequestDetail(PurchaseRequestRead):
    lines: list[PurchaseRequestLineCreate]
    current_state: str | None = None
    current_owner: str | None = None
    current_role: str | None = None


class DashboardSummary(BaseModel):
    purchase_requests_by_status: dict[str, int]
    rfqs_by_status: dict[str, int]
    purchase_orders_by_status: dict[str, int]
    sales_orders_by_status: dict[str, int]
    sales_deliveries_by_status: dict[str, int]
    sales_invoices_by_status: dict[str, int]
    collections_by_status: dict[str, int]
    open_alerts: int
    overdue_workflow_instances: int
    escalated_workflow_instances: int
    workflow_instances: int
