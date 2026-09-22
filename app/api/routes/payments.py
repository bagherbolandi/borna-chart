from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_config_registry, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.payment import PaymentAction, PaymentCreate, PaymentRead
from app.services.config_registry import ConfigRegistry
from app.services.downstream_procurement_service import DownstreamProcurementService
from app.services.rfq_service import ProcurementFlowError

router = APIRouter()


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("AP Accountant")),
) -> PaymentRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return DownstreamProcurementService(db, registry).create_payment(payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{payment_id}/approve", response_model=PaymentRead)
def approve_payment(
    payment_id: int,
    payload: PaymentAction,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Finance Manager")),
) -> PaymentRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return DownstreamProcurementService(db, registry).approve_payment(payment_id, payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{payment_id}/execute", response_model=PaymentRead)
def execute_payment(
    payment_id: int,
    payload: PaymentAction,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Treasury Officer")),
) -> PaymentRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return DownstreamProcurementService(db, registry).execute_payment(payment_id, payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[PaymentRead])
def list_payments(
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> list[PaymentRead]:
    return DownstreamProcurementService(db, registry).list_payments()


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> PaymentRead:
    payment = DownstreamProcurementService(db, registry).get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="payment not found")
    return payment
