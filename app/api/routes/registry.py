from fastapi import APIRouter, Depends

from app.api.deps import get_config_registry, get_current_user
from app.models.master import User
from app.services.config_registry import ConfigRegistry

router = APIRouter()


@router.get("/workflows")
def list_workflows(
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
):
    return registry.get_workflows()


@router.get("/rules")
def list_rules(
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
):
    return registry.get_business_rules()


@router.get("/sla")
def list_sla(
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
):
    return registry.get_sla_profiles()


@router.get("/doa")
def list_doa(
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
):
    return registry.get_doa_matrix()


@router.get("/sod")
def list_sod(
    registry: ConfigRegistry = Depends(get_config_registry),
    _: User = Depends(get_current_user),
):
    return registry.get_sod_matrix()
