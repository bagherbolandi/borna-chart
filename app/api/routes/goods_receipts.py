from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_config_registry, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.goods_receipt import GoodsReceiptCreate, GoodsReceiptRead
from app.services.config_registry import ConfigRegistry
from app.services.downstream_procurement_service import DownstreamProcurementService
from app.services.rfq_service import ProcurementFlowError

router = APIRouter()


@router.post("", response_model=GoodsReceiptRead, status_code=status.HTTP_201_CREATED)
def create_goods_receipt(
    payload: GoodsReceiptCreate,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Warehouse Receiver")),
) -> GoodsReceiptRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return DownstreamProcurementService(db, registry).create_goods_receipt(payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[GoodsReceiptRead])
def list_goods_receipts(
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> list[GoodsReceiptRead]:
    return DownstreamProcurementService(db, registry).list_receipts()


@router.get("/{receipt_id}", response_model=GoodsReceiptRead)
def get_goods_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> GoodsReceiptRead:
    receipt = DownstreamProcurementService(db, registry).get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="goods receipt not found")
    return receipt
