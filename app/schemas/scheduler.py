from pydantic import BaseModel


class SchedulerRunResponse(BaseModel):
    scanned_instances: int
    overdue_instances: int
    escalated_instances: int
    resolved_alerts: int
    created_alerts: int
