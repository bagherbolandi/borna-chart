from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.sales import SalesOrderAction, SalesOrderCreate, SalesOrderRead
from app.services.config_registry import get_registry
from app.services.pricing_sales_service import PricingSalesService, SalesFlowError
from app.services.sales_fulfillment_service import SalesFulfillmentService

router = APIRouter()


@router.post("", response_model=SalesOrderRead, status_code=status.HTTP_201_CREATED)
def create_sales_order(
    payload: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Sales Officer")),
) -> SalesOrderRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return PricingSalesService(db, get_registry()).create_sales_order(payload)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{sales_order_id}/confirm", response_model=SalesOrderRead)
def confirm_sales_order(
    sales_order_id: int,
    payload: SalesOrderAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Sales Manager")),
) -> SalesOrderRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return PricingSalesService(db, get_registry()).confirm_sales_order(sales_order_id, payload.actor, payload.actor_role, payload.note)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{sales_order_id}/review-profitability", response_model=SalesOrderRead)
def review_profitability(
    sales_order_id: int,
    payload: SalesOrderAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Pricing Analyst", "Finance Manager")),
) -> SalesOrderRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SalesFulfillmentService(db, get_registry()).review_profitability(sales_order_id, payload.actor, payload.actor_role, payload.note)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{sales_order_id}/close", response_model=SalesOrderRead)
def close_sales_order(
    sales_order_id: int,
    payload: SalesOrderAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Sales Manager")),
) -> SalesOrderRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SalesFulfillmentService(db, get_registry()).close_sales_order(sales_order_id, payload.actor, payload.actor_role, payload.note)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[SalesOrderRead])
def list_sales_orders(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SalesOrderRead]:
    return PricingSalesService(db, get_registry()).list_sales_orders()


@router.get("/{sales_order_id}", response_model=SalesOrderRead)
def get_sales_order(
    sales_order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SalesOrderRead:
    row = PricingSalesService(db, get_registry()).get_sales_order(sales_order_id)
    if not row:
        raise HTTPException(status_code=404, detail="sales order not found")
    return row
