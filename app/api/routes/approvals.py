from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.master import User
from app.schemas.approval import ApprovalRead
from app.services.approval_service import ApprovalService

router = APIRouter()


@router.get("/{object_type}/{object_id}", response_model=list[ApprovalRead])
def list_approvals(
    object_type: str,
    object_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ApprovalRead]:
    return ApprovalService(db).list_for_object(object_type, object_id)
