from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.alert import AlertRead
from app.services.alert_service import AlertService

router = APIRouter()


@router.get("", response_model=list[AlertRead])
def list_alerts(
    status: str | None = None,
    mine_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlertRead]:
    owner = current_user.username if mine_only else None
    return AlertService(db).list_alerts(owner=owner, status=status)


@router.get("/my", response_model=list[AlertRead])
def my_alerts(
    status: str | None = "open",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlertRead]:
    return AlertService(db).list_alerts(owner=current_user.username, status=status)
