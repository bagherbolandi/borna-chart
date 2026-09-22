from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_config_registry, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderRead
from app.services.config_registry import ConfigRegistry
from app.services.rfq_service import ProcurementFlowError, RFQService

router = APIRouter()


@router.post("", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Procurement Officer")),
) -> PurchaseOrderRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return RFQService(db, registry).create_purchase_order(payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[PurchaseOrderRead])
def list_purchase_orders(
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> list[PurchaseOrderRead]:
    return RFQService(db, registry).list_purchase_orders()


@router.get("/{po_id}", response_model=PurchaseOrderRead)
def get_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> PurchaseOrderRead:
    po = RFQService(db, registry).get_purchase_order(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="purchase order not found")
    return po
