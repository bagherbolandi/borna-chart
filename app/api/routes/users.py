from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.auth import PasswordResetResponse, UserCreate, UserRead
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


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> list[UserRead]:
    return db.query(User).order_by(User.id.asc()).all()
