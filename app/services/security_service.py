from __future__ import annotations

import hashlib
import secrets
import string
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.master import User
from app.models.security import AuthToken
from app.schemas.security_session import SessionInventoryResponse, SessionRead
from app.services.audit_service import AuditService


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


class SecurityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
        return f"{salt}${digest}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            salt, digest = password_hash.split("$", 1)
        except ValueError:
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
        return secrets.compare_digest(candidate, digest)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def validate_password_policy(self, password: str, *, bypass: bool = False) -> None:
        if bypass:
            return
        errors: list[str] = []
        if len(password) < settings.password_min_length:
            errors.append(f"minimum length is {settings.password_min_length}")
        if settings.password_require_upper and not any(ch.isupper() for ch in password):
            errors.append("at least one uppercase letter is required")
        if settings.password_require_lower and not any(ch.islower() for ch in password):
            errors.append("at least one lowercase letter is required")
        if settings.password_require_digit and not any(ch.isdigit() for ch in password):
            errors.append("at least one digit is required")
        if settings.password_require_special and not any(ch in string.punctuation for ch in password):
            errors.append("at least one special character is required")
        if errors:
            raise AuthError("password policy violation: " + "; ".join(errors), status_code=409)

    def log_security_event(self, *, username: str | None, action: str, reason: str | None = None) -> None:
        self.audit.log(
            user_name=username,
            entity_name="auth",
            entity_id=username or "anonymous",
            action=action,
            reason=reason,
        )

    def _is_locked(self, user: User) -> bool:
        return bool(user.locked_until and datetime.fromisoformat(user.locked_until) > self._now())

    def _register_failed_login(self, user: User | None, username: str) -> None:
        if not user:
            self.log_security_event(username=username, action="login_failed", reason="unknown user or invalid credentials")
            return

        user.failed_login_attempts += 1
        user.modified_by = username
        lock_reason = f"failed attempts={user.failed_login_attempts}"
        self.log_security_event(username=username, action="login_failed", reason=lock_reason)
        if user.failed_login_attempts >= settings.max_failed_login_attempts:
            user.locked_until = (self._now() + timedelta(minutes=settings.account_lock_minutes)).isoformat()
            self.log_security_event(
                username=username,
                action="account_locked",
                reason=f"locked until {user.locked_until}",
            )

    def _reset_login_state(self, user: User) -> None:
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = self._now().isoformat()

    def create_user(
        self,
        *,
        username: str,
        password: str,
        full_name: str,
        role_code: str,
        department_code: str | None = None,
        status: str = "active",
        created_by: str | None = None,
        bypass_password_policy: bool = False,
        password_reset_required: bool = False,
    ) -> User:
        existing = self.db.query(User).filter(User.username == username).first()
        if existing:
            raise AuthError("user already exists")
        self.validate_password_policy(password, bypass=bypass_password_policy)
        now = self._now().isoformat()
        user = User(
            username=username,
            password_hash=self.hash_password(password),
            full_name=full_name,
            department_code=department_code,
            role_code=role_code,
            status=status,
            failed_login_attempts=0,
            locked_until=None,
            last_login_at=None,
            password_changed_at=now if not password_reset_required else None,
            password_reset_required=password_reset_required,
            created_by=created_by or username,
            modified_by=created_by or username,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def authenticate(self, username: str, password: str) -> User:
        user = self.db.query(User).filter(User.username == username).first()
        if user and self._is_locked(user):
            self.log_security_event(username=username, action="login_blocked", reason=f"locked until {user.locked_until}")
            raise AuthError("account temporarily locked due to repeated failed login attempts", status_code=423)
        if not user or user.status != "active" or not user.password_hash or not self.verify_password(password, user.password_hash):
            self._register_failed_login(user, username)
            raise AuthError("invalid credentials")

        self._reset_login_state(user)
        reason = f"role={user.role_code}; password_reset_required={user.password_reset_required}"
        self.log_security_event(username=username, action="login_success", reason=reason)
        return user

    def issue_token(self, username: str, hours: int | None = None) -> str:
        token = secrets.token_urlsafe(32)
        now = self._now()
        row = AuthToken(
            token=token,
            username=username,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(hours=hours or settings.auth_token_ttl_hours)).isoformat(),
            revoked_at=None,
        )
        self.db.add(row)
        self.db.flush()
        return token

    def revoke_token(self, token: str, actor: str | None = None) -> None:
        row = self.db.query(AuthToken).filter(AuthToken.token == token).first()
        if not row:
            self.log_security_event(username=actor, action="logout_failed", reason="token not found")
            raise AuthError("invalid token")
        if not row.revoked_at:
            row.revoked_at = self._now().isoformat()
            self.log_security_event(username=actor or row.username, action="logout", reason="token revoked")
        self.db.flush()

    def revoke_all_tokens_for_user(self, username: str, *, actor: str, reason: str) -> int:
        revoked = 0
        rows = self.db.query(AuthToken).filter(AuthToken.username == username, AuthToken.revoked_at.is_(None)).all()
        for row in rows:
            row.revoked_at = self._now().isoformat()
            revoked += 1
        if revoked:
            self.log_security_event(username=actor, action="session_revoke_all", reason=f"target={username}; {reason}; count={revoked}")
        self.db.flush()
        return revoked

    def revoke_session(self, session_id: int, *, actor: str) -> AuthToken:
        row = self.db.query(AuthToken).filter(AuthToken.id == session_id).first()
        if not row:
            raise AuthError("session not found", status_code=404)
        if not row.revoked_at:
            row.revoked_at = self._now().isoformat()
            self.log_security_event(username=actor, action="session_revoked", reason=f"session_id={session_id}; username={row.username}")
        self.db.flush()
        return row

    def change_password(self, *, user: User, current_password: str, new_password: str, actor: str, current_token: str | None = None) -> None:
        if not user.password_hash or not self.verify_password(current_password, user.password_hash):
            self.log_security_event(username=actor, action="password_change_failed", reason="current password mismatch")
            raise AuthError("current password is invalid", status_code=409)
        self.validate_password_policy(new_password)
        if self.verify_password(new_password, user.password_hash):
            raise AuthError("new password must be different from current password", status_code=409)
        user.password_hash = self.hash_password(new_password)
        user.password_changed_at = self._now().isoformat()
        user.password_reset_required = False
        user.modified_by = actor
        revoked = 0
        rows = self.db.query(AuthToken).filter(AuthToken.username == user.username, AuthToken.revoked_at.is_(None)).all()
        for row in rows:
            if current_token and row.token == current_token:
                continue
            row.revoked_at = self._now().isoformat()
            revoked += 1
        self.log_security_event(username=actor, action="password_changed", reason=f"revoked_other_sessions={revoked}")
        self.db.flush()

    def force_password_reset(self, *, username: str, actor: str) -> User:
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise AuthError("user not found", status_code=404)
        user.password_reset_required = True
        user.modified_by = actor
        self.revoke_all_tokens_for_user(username, actor=actor, reason="forced password reset")
        self.log_security_event(username=actor, action="force_password_reset", reason=f"target={username}")
        self.db.flush()
        return user

    def _token_active(self, row: AuthToken) -> bool:
        if row.revoked_at:
            return False
        return datetime.fromisoformat(row.expires_at) > self._now()

    def session_inventory(self, *, actor: str, username: str | None = None, current_token: str | None = None) -> SessionInventoryResponse:
        target_username = username or actor
        rows = self.db.query(AuthToken).filter(AuthToken.username == target_username).order_by(AuthToken.id.desc()).all()
        items = [
            SessionRead(
                id=row.id,
                username=row.username,
                created_at=row.created_at,
                expires_at=row.expires_at,
                revoked_at=row.revoked_at,
                is_active=self._token_active(row),
                is_current=bool(current_token and row.token == current_token),
            )
            for row in rows
        ]
        return SessionInventoryResponse(total_count=len(items), items=items)

    def get_user_by_token(self, token: str) -> User:
        row = self.db.query(AuthToken).filter(AuthToken.token == token).first()
        if not row:
            self.log_security_event(username=None, action="invalid_token", reason="token not found")
            raise AuthError("invalid token")
        if row.revoked_at:
            self.log_security_event(username=row.username, action="revoked_token", reason="revoked token used")
            raise AuthError("token revoked")
        if datetime.fromisoformat(row.expires_at) < self._now():
            self.log_security_event(username=row.username, action="expired_token", reason="expired token used")
            raise AuthError("token expired")
        user = self.db.query(User).filter(User.username == row.username, User.status == "active").first()
        if not user:
            self.log_security_event(username=row.username, action="invalid_token_user", reason="user not found or inactive")
            raise AuthError("user not found or inactive")
        return user

    def seed_demo_users(self) -> None:
        seeds = [
            ("master.admin", "Master Admin", "Master Data Admin", "admin"),
            ("ali", "Ali", "Requester", "ops"),
            ("reza", "Reza", "Requester", "ops"),
            ("sara", "Sara", "Requester", "production"),
            ("mina", "Mina", "Requester", "engineering"),
            ("demo.user", "Demo User", "Requester", "ops"),
            ("manager.1", "Department Manager", "Department Manager", "ops"),
            ("buyer.1", "Buyer One", "Procurement Officer", "procurement"),
            ("buyer.2", "Buyer Two", "Procurement Officer", "procurement"),
            ("proc.mgr", "Procurement Manager", "Procurement Manager", "procurement"),
            ("tech.1", "Technical One", "Technical Evaluator", "engineering"),
            ("tech.2", "Technical Two", "Technical Evaluator", "engineering"),
            ("tech.3", "Technical Three", "Technical Evaluator", "engineering"),
            ("warehouse.1", "Warehouse One", "Warehouse Receiver", "warehouse"),
            ("warehouse.2", "Warehouse Two", "Warehouse Receiver", "warehouse"),
            ("warehouse.3", "Warehouse Three", "Warehouse Receiver", "warehouse"),
            ("qc.1", "QC One", "QC Inspector", "quality"),
            ("qc.2", "QC Two", "QC Inspector", "quality"),
            ("qc.3", "QC Three", "QC Inspector", "quality"),
            ("ap.1", "AP One", "AP Accountant", "finance"),
            ("ap.2", "AP Two", "AP Accountant", "finance"),
            ("ap.3", "AP Three", "AP Accountant", "finance"),
            ("finance.1", "Finance Manager", "Finance Manager", "finance"),
            ("treasury.1", "Treasury One", "Treasury Officer", "treasury"),
            ("pricing.1", "Pricing Analyst", "Pricing Analyst", "sales"),
            ("sales.1", "Sales Officer", "Sales Officer", "sales"),
            ("sales.mgr", "Sales Manager", "Sales Manager", "sales"),
            ("credit.1", "Credit Controller", "Credit Controller", "finance"),
            ("planning.1", "Planning Officer", "Planning Officer", "planning"),
            ("logistics.1", "Logistics Officer", "Logistics Officer", "logistics"),
            ("ar.1", "AR Accountant", "AR Accountant", "finance"),
            ("collect.1", "Collections Officer", "Collections Officer", "finance"),
            ("security.1", "Security Officer", "Security Officer", "security"),
        ]
        for username, full_name, role_code, department_code in seeds:
            existing = self.db.query(User).filter(User.username == username).first()
            if existing:
                continue
            self.create_user(
                username=username,
                password=username,
                full_name=full_name,
                role_code=role_code,
                department_code=department_code,
                created_by="system",
                bypass_password_policy=True,
            )
        self.db.commit()
