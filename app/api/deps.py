from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.config_registry import ConfigRegistry, get_registry
from app.services.security_service import AuthError, SecurityService
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.models.master import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_config_registry() -> ConfigRegistry:
    return get_registry()


def _resolve_token(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str | None:
    if credentials and credentials.credentials:
        return credentials.credentials
    header_token = request.headers.get("x-access-token")
    if header_token:
        return header_token.strip()
    query_token = request.query_params.get("access_token")
    if query_token:
        return query_token.strip()
    return None


def get_bearer_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    token = _resolve_token(request, credentials)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    return token


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = _resolve_token(request, credentials)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    try:
        user = SecurityService(db).get_user_by_token(token)
        allowed_when_reset_required = {
            "/api/v1/auth/me",
            "/api/v1/auth/logout",
            "/api/v1/auth/change-password",
        }
        if user.password_reset_required and request.url.path not in allowed_when_reset_required:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="password change required before using operational endpoints")
        return user
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_code not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{current_user.role_code}' is not allowed",
            )
        return current_user

    return dependency


def ensure_actor_identity(current_user: User, actor: str | None = None, actor_role: str | None = None) -> None:
    if actor and actor != current_user.username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="actor must match authenticated user")
    if actor_role and actor_role != current_user.role_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="actor role must match authenticated role")
