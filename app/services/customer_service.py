from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.master import Customer
from app.services.audit_service import AuditService


class CustomerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def create(self, payload) -> Customer:
        customer = Customer(
            code=payload.code,
            name=payload.name,
            payment_terms=payload.payment_terms,
            credit_limit=Decimal(str(payload.credit_limit)),
            credit_status=payload.credit_status,
            created_by=payload.created_by or "system",
            modified_by=payload.created_by or "system",
        )
        self.db.add(customer)
        self.db.flush()
        self.audit.log(
            user_name=payload.created_by or "system",
            entity_name="customers",
            entity_id=str(customer.id),
            action="create",
            new_value=customer.code,
        )
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def list(self) -> list[Customer]:
        return self.db.query(Customer).order_by(Customer.id.desc()).all()

    def get(self, customer_id: int) -> Customer | None:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
