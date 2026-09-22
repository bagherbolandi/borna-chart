from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.master import User
from app.schemas.traceability import TraceabilityResponse
from app.services.traceability_service import TraceabilityError, TraceabilityService

router = APIRouter()


@router.get("/purchase-requests/{pr_id}", response_model=TraceabilityResponse)
def procurement_traceability(
    pr_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TraceabilityResponse:
    try:
        return TraceabilityService(db).procurement_traceability(pr_id)
    except TraceabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sales-orders/{sales_order_id}", response_model=TraceabilityResponse)
def sales_traceability(
    sales_order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TraceabilityResponse:
    try:
        return TraceabilityService(db).sales_traceability(sales_order_id)
    except TraceabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/document/{object_type}/{object_id}", response_model=TraceabilityResponse)
def document_traceability(
    object_type: str,
    object_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TraceabilityResponse:
    try:
        return TraceabilityService(db).document_traceability(object_type, object_id)
    except TraceabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
