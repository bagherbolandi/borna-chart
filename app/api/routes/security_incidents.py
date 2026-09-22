from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_actor_identity, require_roles
from app.core.db import get_db
from app.models.master import User
from app.schemas.security_incident import SecurityIncidentAction, SecurityIncidentCreate, SecurityIncidentRead
from app.services.config_registry import get_registry
from app.services.security_incident_service import SecurityIncidentError, SecurityIncidentService

router = APIRouter()


@router.post("", response_model=SecurityIncidentRead, status_code=status.HTTP_201_CREATED)
def create_security_incident(
    payload: SecurityIncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> SecurityIncidentRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SecurityIncidentService(db, get_registry()).create_incident(payload)
    except SecurityIncidentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{incident_id}/triage", response_model=SecurityIncidentRead)
def triage_security_incident(
    incident_id: int,
    payload: SecurityIncidentAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> SecurityIncidentRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SecurityIncidentService(db, get_registry()).triage_incident(incident_id, payload)
    except SecurityIncidentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{incident_id}/contain", response_model=SecurityIncidentRead)
def contain_security_incident(
    incident_id: int,
    payload: SecurityIncidentAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> SecurityIncidentRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SecurityIncidentService(db, get_registry()).contain_incident(incident_id, payload)
    except SecurityIncidentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{incident_id}/resolve", response_model=SecurityIncidentRead)
def resolve_security_incident(
    incident_id: int,
    payload: SecurityIncidentAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> SecurityIncidentRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SecurityIncidentService(db, get_registry()).resolve_incident(incident_id, payload)
    except SecurityIncidentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{incident_id}/close", response_model=SecurityIncidentRead)
def close_security_incident(
    incident_id: int,
    payload: SecurityIncidentAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> SecurityIncidentRead:
    ensure_actor_identity(current_user, payload.actor, payload.actor_role)
    try:
        return SecurityIncidentService(db, get_registry()).close_incident(incident_id, payload)
    except SecurityIncidentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[SecurityIncidentRead])
def list_security_incidents(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> list[SecurityIncidentRead]:
    return SecurityIncidentService(db, get_registry()).list_incidents()


@router.get("/{incident_id}", response_model=SecurityIncidentRead)
def get_security_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Security Officer", "Master Data Admin")),
) -> SecurityIncidentRead:
    row = SecurityIncidentService(db, get_registry()).get_incident(incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="security incident not found")
    return row
