from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_bearer_token, get_current_user
from app.core.config import settings
from app.core.db import get_db
from app.models.master import User
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    PasswordChangeRequest,
    PasswordResetResponse,
    TokenResponse,
    UserRead,
)
from app.services.rate_limit_service import RateLimitService
from app.services.security_service import AuthError, SecurityService

router = APIRouter()


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    service = SecurityService(db)
    client_ip = _client_ip(request)
    rate_limit_key = f"login:{client_ip}:{payload.username.strip().lower()}"
    allowed, retry_after = RateLimitService.allow(
        key=rate_limit_key,
        limit=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    if not allowed:
        service.log_security_event(
            username=payload.username,
            action="rate_limit_block",
            reason=f"ip={client_ip}; retry_after={retry_after}",
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many login attempts, retry later",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        user = service.authenticate(payload.username, payload.password)
        token = service.issue_token(user.username)
        db.commit()
        return TokenResponse(access_token=token, password_reset_required=bool(user.password_reset_required))
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/logout", response_model=LogoutResponse)
def logout(
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    service = SecurityService(db)
    try:
        service.revoke_token(token, actor=current_user.username)
        db.commit()
        return LogoutResponse(detail="logged out")
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/change-password", response_model=PasswordResetResponse)
def change_password(
    payload: PasswordChangeRequest,
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    service = SecurityService(db)
    try:
        service.change_password(
            user=current_user,
            current_password=payload.current_password,
            new_password=payload.new_password,
            actor=current_user.username,
            current_token=token,
        )
        db.commit()
        return PasswordResetResponse(detail="password changed")
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return current_user
