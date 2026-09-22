from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.master import User
from app.models.workflow import WorkflowInstance
from app.services.config_registry import get_registry

router = APIRouter()


@router.get("/my-tasks")
def my_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(WorkflowInstance)
        .filter(WorkflowInstance.current_owner == current_user.username, WorkflowInstance.status == "open")
        .order_by(WorkflowInstance.id.desc())
        .all()
    )
    return [
        {
            "workflow_instance_id": item.id,
            "object_type": item.object_type,
            "object_id": item.object_id,
            "process_name": item.process_name,
            "current_state": item.current_state,
            "current_owner": item.current_owner,
            "current_role": item.current_role,
            "financial_impact": float(item.financial_impact),
        }
        for item in items
    ]


@router.get("/approvals")
def approval_inbox(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workflows = get_registry().get_workflows()
    open_items = db.query(WorkflowInstance).filter(WorkflowInstance.status == "open").order_by(WorkflowInstance.id.desc()).all()
    results = []
    for item in open_items:
        config = workflows.get(item.process_name)
        if not config:
            continue
        actions = []
        for transition in config.get("transitions", []):
            if transition["from"] == item.current_state and current_user.role_code in transition.get("roles", []):
                actions.append(transition["action"])
        if actions:
            results.append(
                {
                    "workflow_instance_id": item.id,
                    "object_type": item.object_type,
                    "object_id": item.object_id,
                    "process_name": item.process_name,
                    "current_state": item.current_state,
                    "available_actions": actions,
                    "financial_impact": float(item.financial_impact),
                    "current_owner": item.current_owner,
                }
            )
    return results
