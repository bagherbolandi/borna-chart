from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.supplier import SupplierCreate, SupplierRead
from app.services.supplier_service import SupplierService

router = APIRouter()


@router.post("", response_model=SupplierRead)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin")),
) -> SupplierRead:
    if payload.created_by and payload.created_by != current_user.username:
        payload.created_by = current_user.username
    elif not payload.created_by:
        payload.created_by = current_user.username
    return SupplierService(db).create(payload)


@router.get("", response_model=list[SupplierRead])
def list_suppliers(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SupplierRead]:
    return SupplierService(db).list()
