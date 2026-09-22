from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.collection import CollectionReceiptCreate, CollectionReceiptRead
from app.services.config_registry import get_registry
from app.services.pricing_sales_service import SalesFlowError
from app.services.sales_fulfillment_service import SalesFulfillmentService

router = APIRouter()


@router.post("", response_model=CollectionReceiptRead, status_code=status.HTTP_201_CREATED)
def create_collection_receipt(
    payload: CollectionReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Collections Officer")),
) -> CollectionReceiptRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SalesFulfillmentService(db, get_registry()).create_collection_receipt(payload)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[CollectionReceiptRead])
def list_collection_receipts(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CollectionReceiptRead]:
    return SalesFulfillmentService(db, get_registry()).list_collections()


@router.get("/{collection_id}", response_model=CollectionReceiptRead)
def get_collection_receipt(
    collection_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CollectionReceiptRead:
    row = SalesFulfillmentService(db, get_registry()).get_collection(collection_id)
    if not row:
        raise HTTPException(status_code=404, detail="collection receipt not found")
    return row
