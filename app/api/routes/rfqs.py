from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_config_registry, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.action import ActorAction
from app.schemas.rfq import CommercialEvaluationAction, QuotationCreate, QuotationRead, RFQCreate, RFQDetail, RFQRead
from app.services.config_registry import ConfigRegistry
from app.services.rfq_service import ProcurementFlowError, RFQService

router = APIRouter()


@router.post("", response_model=RFQRead, status_code=status.HTTP_201_CREATED)
def create_rfq(
    payload: RFQCreate,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Procurement Officer")),
) -> RFQRead:
    if payload.buyer != current_user.username:
        raise HTTPException(status_code=403, detail="buyer must match authenticated user")
    if payload.created_by and payload.created_by != current_user.username:
        raise HTTPException(status_code=403, detail="created_by must match authenticated user")
    try:
        return RFQService(db, registry).create_rfq(payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[RFQRead])
def list_rfqs(
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> list[RFQRead]:
    return RFQService(db, registry).list_rfqs()


@router.get("/{rfq_id}", response_model=RFQDetail)
def get_rfq(
    rfq_id: int,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> RFQDetail:
    service = RFQService(db, registry)
    rfq = service.get_rfq(rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="rfq not found")
    instance = service.get_workflow_instance(rfq.workflow_instance_id)
    return RFQDetail(
        **RFQRead.model_validate(rfq).model_dump(),
        current_state=instance.current_state if instance else None,
        current_owner=instance.current_owner if instance else None,
        current_role=instance.current_role if instance else None,
        quotations=[QuotationRead.model_validate(item) for item in service.get_quotes(rfq_id)],
    )


@router.post("/{rfq_id}/quotations", response_model=QuotationRead, status_code=status.HTTP_201_CREATED)
def add_quotation(
    rfq_id: int,
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Procurement Officer")),
) -> QuotationRead:
    if payload.created_by and payload.created_by != current_user.username:
        raise HTTPException(status_code=403, detail="created_by must match authenticated user")
    try:
        return RFQService(db, registry).add_quotation(rfq_id, payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{rfq_id}/record-quotes", response_model=RFQRead)
def record_quotes(
    rfq_id: int,
    payload: ActorAction,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Procurement Officer")),
) -> RFQRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return RFQService(db, registry).mark_quotation_received(
            rfq_id=rfq_id,
            actor=payload.actor,
            actor_role=payload.actor_role,
            exception_approved=payload.exception_approved,
        )
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{rfq_id}/commercial-evaluate", response_model=RFQRead)
def commercial_evaluate(
    rfq_id: int,
    payload: CommercialEvaluationAction,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Procurement Officer")),
) -> RFQRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return RFQService(db, registry).commercial_evaluate(rfq_id, payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{rfq_id}/technical-approve", response_model=RFQRead)
def technical_approve(
    rfq_id: int,
    payload: ActorAction,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Technical Evaluator")),
) -> RFQRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return RFQService(db, registry).technical_approve(rfq_id, payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{rfq_id}/price-approve", response_model=RFQRead)
def price_approve(
    rfq_id: int,
    payload: ActorAction,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Procurement Manager", "Finance Manager")),
) -> RFQRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return RFQService(db, registry).price_approve(rfq_id, payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
