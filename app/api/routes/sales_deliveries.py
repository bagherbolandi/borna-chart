from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.sales_delivery import SalesDeliveryCreate, SalesDeliveryExecute, SalesDeliveryRead, SalesDeliveryRelease
from app.services.config_registry import get_registry
from app.services.pricing_sales_service import SalesFlowError
from app.services.sales_fulfillment_service import SalesFulfillmentService

router = APIRouter()


@router.post("", response_model=SalesDeliveryRead, status_code=status.HTTP_201_CREATED)
def create_sales_delivery(
    payload: SalesDeliveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Planning Officer")),
) -> SalesDeliveryRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SalesFulfillmentService(db, get_registry()).create_delivery_plan(payload)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{delivery_id}/release", response_model=SalesDeliveryRead)
def release_sales_delivery(
    delivery_id: int,
    payload: SalesDeliveryRelease,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Planning Officer", "Warehouse Receiver")),
) -> SalesDeliveryRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SalesFulfillmentService(db, get_registry()).release_delivery(delivery_id, payload)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{delivery_id}/deliver", response_model=SalesDeliveryRead)
def execute_sales_delivery(
    delivery_id: int,
    payload: SalesDeliveryExecute,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Logistics Officer")),
) -> SalesDeliveryRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SalesFulfillmentService(db, get_registry()).deliver(delivery_id, payload)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[SalesDeliveryRead])
def list_sales_deliveries(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SalesDeliveryRead]:
    return SalesFulfillmentService(db, get_registry()).list_deliveries()


@router.get("/{delivery_id}", response_model=SalesDeliveryRead)
def get_sales_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SalesDeliveryRead:
    row = SalesFulfillmentService(db, get_registry()).get_delivery(delivery_id)
    if not row:
        raise HTTPException(status_code=404, detail="sales delivery not found")
    return row
