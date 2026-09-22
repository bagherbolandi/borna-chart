from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_config_registry, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.quality import QualityInspectionCreate, QualityInspectionFinalize, QualityInspectionRead
from app.services.config_registry import ConfigRegistry
from app.services.downstream_procurement_service import DownstreamProcurementService
from app.services.rfq_service import ProcurementFlowError

router = APIRouter()


@router.post("", response_model=QualityInspectionRead, status_code=status.HTTP_201_CREATED)
def create_quality_inspection(
    payload: QualityInspectionCreate,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("QC Inspector")),
) -> QualityInspectionRead:
    if payload.inspector != current_user.username:
        raise HTTPException(status_code=403, detail="inspector must match authenticated user")
    try:
        return DownstreamProcurementService(db, registry).create_quality_inspection(payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{qc_id}/finalize", response_model=QualityInspectionRead)
def finalize_quality_inspection(
    qc_id: int,
    payload: QualityInspectionFinalize,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("QC Inspector")),
) -> QualityInspectionRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return DownstreamProcurementService(db, registry).finalize_quality_inspection(qc_id, payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[QualityInspectionRead])
def list_quality_inspections(
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> list[QualityInspectionRead]:
    return DownstreamProcurementService(db, registry).list_quality_inspections()


@router.get("/{qc_id}", response_model=QualityInspectionRead)
def get_quality_inspection(
    qc_id: int,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> QualityInspectionRead:
    qc = DownstreamProcurementService(db, registry).get_quality_inspection(qc_id)
    if not qc:
        raise HTTPException(status_code=404, detail="quality inspection not found")
    return qc
