from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.pricing import PriceApprovalAction, PriceListCreate, PriceListRead
from app.services.config_registry import get_registry
from app.services.pricing_sales_service import PricingSalesService, SalesFlowError

router = APIRouter()


@router.post("", response_model=PriceListRead, status_code=status.HTTP_201_CREATED)
def create_price_list(
    payload: PriceListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Pricing Analyst")),
) -> PriceListRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return PricingSalesService(db, get_registry()).create_price_list(payload)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{price_list_id}/approve", response_model=PriceListRead)
def approve_price_list(
    price_list_id: int,
    payload: PriceApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Pricing Analyst", "Sales Manager", "Finance Manager")),
) -> PriceListRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return PricingSalesService(db, get_registry()).approve_price_list(price_list_id, payload.actor, payload.actor_role, payload.note)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[PriceListRead])
def list_price_lists(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PriceListRead]:
    return PricingSalesService(db, get_registry()).list_price_lists()


@router.get("/{price_list_id}", response_model=PriceListRead)
def get_price_list(
    price_list_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PriceListRead:
    row = PricingSalesService(db, get_registry()).get_price_list(price_list_id)
    if not row:
        raise HTTPException(status_code=404, detail="price list not found")
    return row
