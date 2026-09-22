from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.sales import Product
from app.services.audit_service import AuditService


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def create(self, payload) -> Product:
        product = Product(
            code=payload.code,
            name=payload.name,
            family=payload.family,
            uom=payload.uom,
            standard_cost=Decimal(str(payload.standard_cost)),
            approved_min_price=Decimal(str(payload.approved_min_price)),
            pricing_method=payload.pricing_method,
            status=payload.status,
            created_by=payload.created_by or "system",
            modified_by=payload.created_by or "system",
        )
        self.db.add(product)
        self.db.flush()
        self.audit.log(
            user_name=payload.created_by or "system",
            entity_name="products",
            entity_id=str(product.id),
            action="create",
            new_value=product.code,
        )
        self.db.commit()
        self.db.refresh(product)
        return product

    def list(self) -> list[Product]:
        return self.db.query(Product).order_by(Product.id.desc()).all()

    def get(self, product_id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == product_id).first()
