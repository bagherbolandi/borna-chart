from pydantic import BaseModel


class WorkflowTransitionResponse(BaseModel):
    from_state: str
    to_state: str
    action: str
    roles: list[str]
    rules: list[str]


class WorkflowDefinitionResponse(BaseModel):
    process: str
    object_type: str
    states: list[dict]
    transitions: list[WorkflowTransitionResponse]
