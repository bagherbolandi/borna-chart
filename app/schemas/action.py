from pydantic import BaseModel


class ActorAction(BaseModel):
    actor: str
    actor_role: str
    note: str | None = None
    exception_approved: bool = False
