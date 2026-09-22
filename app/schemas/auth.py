from pydantic import BaseModel

from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    password_reset_required: bool = False


class LogoutResponse(BaseModel):
    detail: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetResponse(BaseModel):
    detail: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    department_code: str | None = None
    role_code: str
    status: str = "active"


class UserUpdate(BaseModel):
    full_name: str | None = None
    department_code: str | None = None
    role_code: str | None = None
    status: str | None = None


class AdminActionResponse(BaseModel):
    detail: str


class UserRead(ORMModel):
    id: int
    username: str
    full_name: str
    department_code: str | None
    role_code: str | None
    status: str
    last_login_at: str | None = None
    password_changed_at: str | None = None
    password_reset_required: bool = False
