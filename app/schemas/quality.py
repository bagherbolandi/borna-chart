from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class QualityInspectionCreate(BaseModel):
    goods_receipt_id: int
    inspection_date: date
    inspector: str
    actor_role: str = "QC Inspector"


class QualityInspectionFinalize(BaseModel):
    actor: str
    actor_role: str
    result: str
    accepted_qty: float = Field(ge=0)
    rejected_qty: float = Field(ge=0)
    defect_code: str | None = None
    corrective_action: str | None = None
    note: str | None = None


class QualityInspectionRead(ORMModel):
    id: int
    code: str
    goods_receipt_id: int
    inspection_date: str
    inspector: str
    result: str | None
    accepted_qty: float
    rejected_qty: float
    defect_code: str | None
    corrective_action: str | None
    status: str
    workflow_instance_id: int | None
