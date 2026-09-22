from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.sales_invoice import SalesInvoiceCreate, SalesInvoiceRead
from app.services.config_registry import get_registry
from app.services.pricing_sales_service import SalesFlowError
from app.services.sales_fulfillment_service import SalesFulfillmentService

router = APIRouter()


@router.post("", response_model=SalesInvoiceRead, status_code=status.HTTP_201_CREATED)
def create_sales_invoice(
    payload: SalesInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("AR Accountant")),
) -> SalesInvoiceRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SalesFulfillmentService(db, get_registry()).create_sales_invoice(payload)
    except SalesFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[SalesInvoiceRead])
def list_sales_invoices(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SalesInvoiceRead]:
    return SalesFulfillmentService(db, get_registry()).list_sales_invoices()


@router.get("/{invoice_id}", response_model=SalesInvoiceRead)
def get_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SalesInvoiceRead:
    row = SalesFulfillmentService(db, get_registry()).get_sales_invoice(invoice_id)
    if not row:
        raise HTTPException(status_code=404, detail="sales invoice not found")
    return row
