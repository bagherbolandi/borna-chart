from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, get_config_registry, get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.action import ActorAction
from app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestDetail,
    PurchaseRequestRead,
    PurchaseRequestSubmit,
)
from app.services.config_registry import ConfigRegistry
from app.services.purchase_request_service import PurchaseRequestService, RuleViolationError

router = APIRouter()


@router.post("", response_model=PurchaseRequestRead, status_code=status.HTTP_201_CREATED)
def create_purchase_request(
    payload: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Requester")),
) -> PurchaseRequestRead:
    if payload.requester != current_user.username:
        raise HTTPException(status_code=403, detail="requester must match authenticated user")
    if payload.created_by and payload.created_by != current_user.username:
        raise HTTPException(status_code=403, detail="created_by must match authenticated user")
    return PurchaseRequestService(db, registry).create(payload)


@router.get("", response_model=list[PurchaseRequestRead])
def list_purchase_requests(
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> list[PurchaseRequestRead]:
    return PurchaseRequestService(db, registry).list()


@router.get("/{pr_id}", response_model=PurchaseRequestDetail)
def get_purchase_request(
    pr_id: int,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
) -> PurchaseRequestDetail:
    service = PurchaseRequestService(db, registry)
    pr = service.get(pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="purchase request not found")
    lines = service.get_lines(pr_id)
    instance = service.get_workflow_instance(pr.workflow_instance_id)
    return PurchaseRequestDetail(
        **PurchaseRequestRead.model_validate(pr).model_dump(),
        lines=[
            {
                "line_no": line.line_no,
                "description": line.description,
                "material_code": line.material_code,
                "qty": float(line.qty),
                "uom": line.uom,
                "estimated_unit_price": float(line.estimated_unit_price) if line.estimated_unit_price is not None else None,
                "cost_center_code": line.cost_center_code,
            }
            for line in lines
        ],
        current_state=instance.current_state if instance else None,
        current_owner=instance.current_owner if instance else None,
        current_role=instance.current_role if instance else None,
    )


@router.post("/{pr_id}/submit", response_model=PurchaseRequestRead)
def submit_purchase_request(
    pr_id: int,
    payload: PurchaseRequestSubmit,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Requester")),
) -> PurchaseRequestRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return PurchaseRequestService(db, registry).submit(
            pr_id=pr_id,
            actor=payload.actor,
            actor_role=payload.actor_role,
            exception_approved=payload.exception_approved,
        )
    except RuleViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{pr_id}/route-review", response_model=PurchaseRequestRead)
def route_review_purchase_request(
    pr_id: int,
    payload: ActorAction,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Department Manager")),
) -> PurchaseRequestRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return PurchaseRequestService(db, registry).route_review(
            pr_id=pr_id,
            actor=payload.actor,
            actor_role=payload.actor_role,
            note=payload.note,
        )
    except RuleViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{pr_id}/approve", response_model=PurchaseRequestRead)
def approve_purchase_request(
    pr_id: int,
    payload: ActorAction,
    db: Session = Depends(get_db),
    registry: ConfigRegistry = Depends(get_config_registry),
    current_user: User = Depends(require_roles("Department Manager", "Finance Manager")),
) -> PurchaseRequestRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return PurchaseRequestService(db, registry).approve(
            pr_id=pr_id,
            actor=payload.actor,
            actor_role=payload.actor_role,
            note=payload.note,
        )
    except RuleViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
