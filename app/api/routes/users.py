from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.auth import AdminActionResponse, PasswordResetResponse, UserCreate, UserRead, UserUpdate
from app.services.security_service import AuthError, SecurityService

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin")),
) -> UserRead:
    try:
        user = SecurityService(db).create_user(
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
            role_code=payload.role_code,
            department_code=payload.department_code,
            status=payload.status,
            created_by=current_user.username,
        )
        db.commit()
        db.refresh(user)
        return user
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code if exc.status_code != 401 else 409, detail=str(exc)) from exc


@router.post("/{username}/force-password-reset", response_model=PasswordResetResponse)
def force_password_reset(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> PasswordResetResponse:
    try:
        SecurityService(db).force_password_reset(username=username, actor=current_user.username)
        db.commit()
        return PasswordResetResponse(detail="password reset has been forced")
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.patch("/{username}", response_model=UserRead)
def update_user(
    username: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> UserRead:
    try:
        user = SecurityService(db).update_user(
            username=username,
            actor=current_user.username,
            full_name=payload.full_name,
            department_code=payload.department_code,
            role_code=payload.role_code,
            status=payload.status,
        )
        db.commit()
        db.refresh(user)
        return user
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/{username}/unlock", response_model=AdminActionResponse)
def unlock_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> AdminActionResponse:
    try:
        SecurityService(db).unlock_user(username=username, actor=current_user.username)
        db.commit()
        return AdminActionResponse(detail="user unlocked")
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/{username}/revoke-sessions", response_model=AdminActionResponse)
def revoke_user_sessions(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> AdminActionResponse:
    try:
        SecurityService(db).revoke_all_tokens_for_user(username, actor=current_user.username, reason="manual admin session revocation")
        db.commit()
        return AdminActionResponse(detail="all sessions revoked")
    except AuthError as exc:
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> list[UserRead]:
    return db.query(User).order_by(User.id.asc()).all()
