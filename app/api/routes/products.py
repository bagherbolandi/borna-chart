from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import ProductService

router = APIRouter()


@router.post("", response_model=ProductRead)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin")),
) -> ProductRead:
    if not payload.created_by:
        payload.created_by = current_user.username
    return ProductService(db).create(payload)


@router.get("", response_model=list[ProductRead])
def list_products(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ProductRead]:
    return ProductService(db).list()
