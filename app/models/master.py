from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import AuditMixin


class Department(AuditMixin, Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)


class User(AuditMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    department_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_login_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    password_changed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    password_reset_required: Mapped[bool] = mapped_column(default=False, nullable=False)


class Supplier(AuditMixin, Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Customer(AuditMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    credit_limit: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    credit_status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_time: Mapped[str] = mapped_column(String(40), nullable=False)
    user_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    authorized_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
