from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_config_registry, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.supplier_invoice import SupplierInvoiceCreate, SupplierInvoiceMatch, SupplierInvoiceRead
from app.services.config_registry import ConfigRegistry
from app.services.downstream_procurement_service import DownstreamProcurementService
from app.services.rfq_service import ProcurementFlowError

router = APIRouter()


@router.post("", response_model=SupplierInvoiceRead, status_code=status.HTTP_201_CREATED)
def create_supplier_invoice(
    payload: SupplierInvoiceCreate,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("AP Accountant")),
) -> SupplierInvoiceRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return DownstreamProcurementService(db, registry).create_supplier_invoice(payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{invoice_id}/match", response_model=SupplierInvoiceRead)
def match_supplier_invoice(
    invoice_id: int,
    payload: SupplierInvoiceMatch,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("AP Accountant")),
) -> SupplierInvoiceRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return DownstreamProcurementService(db, registry).match_supplier_invoice(invoice_id, payload)
    except ProcurementFlowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[SupplierInvoiceRead])
def list_supplier_invoices(
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> list[SupplierInvoiceRead]:
    return DownstreamProcurementService(db, registry).list_supplier_invoices()


@router.get("/{invoice_id}", response_model=SupplierInvoiceRead)
def get_supplier_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> SupplierInvoiceRead:
    invoice = DownstreamProcurementService(db, registry).get_supplier_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="supplier invoice not found")
    return invoice
