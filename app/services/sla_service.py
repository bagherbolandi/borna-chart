from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.workflow import WorkflowInstance
from app.services.alert_service import AlertService
from app.services.config_registry import ConfigRegistry


@dataclass
class SchedulerResult:
    scanned_instances: int = 0
    overdue_instances: int = 0
    escalated_instances: int = 0
    resolved_alerts: int = 0
    created_alerts: int = 0


class SLAService:
    def __init__(self, db: Session, registry: ConfigRegistry) -> None:
        self.db = db
        self.registry = registry
        self.alerts = AlertService(db)

    def _sla_data(self) -> dict[str, Any]:
        return self.registry.get_sla_profiles()

    def find_profile(self, process_name: str, stage_code: str) -> dict[str, Any] | None:
        data = self._sla_data()
        profiles = data.get("profiles", [])
        for profile in profiles:
            if profile.get("process") == process_name and profile.get("stage") == stage_code:
                return profile
        for profile in profiles:
            if profile.get("stage") == stage_code:
                return profile
        return None

    def get_escalation_profile(self, code: str | None) -> dict[str, Any] | None:
        if not code:
            return None
        data = self._sla_data()
        for profile in data.get("escalation_profiles", []):
            if profile.get("code") == code:
                return profile
        return None

    @staticmethod
    def _parse_duration(value: int, unit: str) -> timedelta:
        if unit in {"business_day", "day", "days"}:
            return timedelta(days=value)
        if unit in {"hour", "hours", "h"}:
            return timedelta(hours=value)
        return timedelta(days=value)

    @staticmethod
    def _parse_after(expr: str) -> timedelta:
        expr = expr.strip().lower()
        if expr.endswith("h"):
            return timedelta(hours=int(expr[:-1] or "0"))
        if expr.endswith("d"):
            return timedelta(days=int(expr[:-1] or "0"))
        return timedelta(hours=int(expr or "0"))

    def assign_due_at(self, instance: WorkflowInstance) -> WorkflowInstance:
        profile = self.find_profile(instance.process_name, instance.current_state)
        if not profile:
            instance.due_at = None
            return instance
        delta = self._parse_duration(int(profile.get("duration", 1)), str(profile.get("unit", "day")))
        instance.due_at = (datetime.now(UTC) + delta).isoformat()
        return instance

    def _severity_for_level(self, level: int) -> str:
        return {1: "low", 2: "medium", 3: "high", 4: "critical"}.get(level, "medium")

    def evaluate_instance(self, instance: WorkflowInstance) -> tuple[int, int, int, bool]:
        if instance.status != "open":
            resolved = self.alerts.resolve_for_object(
                related_object_type=instance.object_type,
                related_object_id=instance.object_id,
            )
            return (0, 0, resolved, False)
        if not instance.due_at:
            return (0, 0, 0, False)

        due_at = datetime.fromisoformat(instance.due_at)
        now = datetime.now(UTC)
        if due_at > now:
            resolved = self.alerts.resolve_for_object(
                related_object_type=instance.object_type,
                related_object_id=instance.object_id,
            )
            if instance.escalation_level != 0:
                instance.escalation_level = 0
                self.db.flush()
            return (0, 0, resolved, False)

        overdue_for = now - due_at
        profile = self.find_profile(instance.process_name, instance.current_state)
        escalation_profile = self.get_escalation_profile(profile.get("escalation_profile") if profile else None)
        target_level = 1
        if escalation_profile:
            target_level = 0
            for level in escalation_profile.get("levels", []):
                if overdue_for >= self._parse_after(str(level.get("after", "0h"))):
                    target_level = max(target_level, int(level.get("level", 1)))
        target_level = max(target_level, 1)

        created = 0
        escalated = False
        if target_level > instance.escalation_level:
            for level in range(instance.escalation_level + 1, target_level + 1):
                alert_code = f"SLA-L{level}"
                if not self.alerts.exists_open_alert(
                    alert_code=alert_code,
                    related_object_type=instance.object_type,
                    related_object_id=instance.object_id,
                ):
                    self.alerts.create(
                        alert_code=alert_code,
                        related_object_type=instance.object_type,
                        related_object_id=instance.object_id,
                        alert_type="SLA Overdue",
                        severity=self._severity_for_level(level),
                        owner=instance.current_owner,
                        financial_impact=float(instance.financial_impact),
                        created_by="scheduler",
                        message=(
                            f"{instance.object_type}#{instance.object_id} in state '{instance.current_state}' "
                            f"is overdue and escalated to level {level}."
                        ),
                        escalation_level=level,
                    )
                    created += 1
            instance.escalation_level = target_level
            self.db.flush()
            escalated = True
        return (1, created, 0, escalated)

    def run_scheduler(self) -> SchedulerResult:
        result = SchedulerResult()
        instances = self.db.query(WorkflowInstance).all()
        result.scanned_instances = len(instances)
        for instance in instances:
            overdue_increment, created, resolved, escalated = self.evaluate_instance(instance)
            result.overdue_instances += overdue_increment
            result.created_alerts += created
            result.resolved_alerts += resolved
            if escalated:
                result.escalated_instances += 1
        self.db.commit()
        return result
