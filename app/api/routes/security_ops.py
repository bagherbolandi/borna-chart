from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_bearer_token, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.security_dashboard import SecurityDashboardSummary, TokenCleanupResult
from app.schemas.security_session import SessionInventoryResponse
from app.services.security_operations_service import SecurityOperationsService
from app.services.security_service import AuthError, SecurityService

router = APIRouter()


@router.get("/dashboard", response_model=SecurityDashboardSummary)
def security_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> SecurityDashboardSummary:
    return SecurityOperationsService(db).dashboard_summary()


@router.post("/tokens/cleanup", response_model=TokenCleanupResult)
def cleanup_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> TokenCleanupResult:
    return SecurityOperationsService(db).cleanup_tokens(actor=current_user.username)


@router.get("/my-sessions", response_model=SessionInventoryResponse)
def my_sessions(
    token: str = Depends(get_bearer_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionInventoryResponse:
    return SecurityService(db).session_inventory(actor=current_user.username, current_token=token)


@router.get("/sessions", response_model=SessionInventoryResponse)
def user_sessions(
    username: str,
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> SessionInventoryResponse:
    return SecurityService(db).session_inventory(actor=current_user.username, username=username, current_token=token)


@router.post("/sessions/{session_id}/revoke", response_model=TokenCleanupResult)
def revoke_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> TokenCleanupResult:
    service = SecurityService(db)
    try:
        row = service.revoke_session(session_id, actor=current_user.username)
        db.commit()
        inventory = service.session_inventory(actor=current_user.username, username=row.username)
        return TokenCleanupResult(
            removed_expired_tokens=0,
            removed_revoked_tokens=1,
            remaining_active_tokens=sum(1 for item in inventory.items if item.is_active),
            detail="session revoked",
        )
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
