from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.scheduler import SchedulerRunResponse
from app.services.config_registry import get_registry
from app.services.sla_service import SLAService

router = APIRouter()


@router.post("/run-sla", response_model=SchedulerRunResponse)
def run_sla_scheduler(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Master Data Admin", "Department Manager", "Finance Manager", "Procurement Manager")),
) -> SchedulerRunResponse:
    result = SLAService(db, get_registry()).run_scheduler()
    return SchedulerRunResponse(
        scanned_instances=result.scanned_instances,
        overdue_instances=result.overdue_instances,
        escalated_instances=result.escalated_instances,
        resolved_alerts=result.resolved_alerts,
        created_alerts=result.created_alerts,
    )
