from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.master import Supplier
from app.services.audit_service import AuditService


class SupplierService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def create(self, payload) -> Supplier:
        supplier = Supplier(
            code=payload.code,
            name=payload.name,
            approval_status=payload.approval_status,
            risk_level=payload.risk_level,
            payment_terms=payload.payment_terms,
            created_by=payload.created_by or "system",
            modified_by=payload.created_by or "system",
        )
        self.db.add(supplier)
        self.db.flush()
        self.audit.log(
            user_name=payload.created_by or "system",
            entity_name="suppliers",
            entity_id=str(supplier.id),
            action="create",
            new_value=supplier.code,
        )
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def list(self) -> list[Supplier]:
        return self.db.query(Supplier).order_by(Supplier.id.desc()).all()

    def get(self, supplier_id: int) -> Supplier | None:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
