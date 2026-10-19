
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from agent.workflow.schemas.error import WorkflowError
from agent.workflow.schemas.result import KnowledgeSource

WorkflowResponseStatus = Literal[
    "pending",
    "running",
    "completed",
    "partial",
    "failed",
]

WorkflowRoute = Literal[
    "mes",
    "rag",
    "bi",
    "general",
    "complex",
]


class WorkflowStepResponse(BaseModel):
    step_id: int
    agent: str
    task: str

    status: Literal["success", "failed"]

    output: str
    duration_ms: float | None = None
    attempts: int = Field(default=1, ge=1)

    error: WorkflowError | None = None

    data: dict[str, Any] | None = None

    sources: list[KnowledgeSource] = Field(
        default_factory=list
    )

    sql: str | None = None

    chart: dict[str, Any] | None = None


class WorkflowChartResponse(BaseModel):
    step_id: int
    agent: str = "bi"
    option: dict[str, Any]


class WorkflowExecutionEventResponse(BaseModel):
    event_type: str
    step_id: int | None = None
    agent: str | None = None
    timestamp: datetime
    duration_ms: float | None = None

    details: dict[str, Any] = Field(
        default_factory=dict
    )


class WorkflowResponse(BaseModel):
    workflow_id: str

    status: WorkflowResponseStatus
    route: WorkflowRoute
    route_reason: str = ""

    answer: str

    steps: list[WorkflowStepResponse] = Field(
        default_factory=list
    )

    sources: list[KnowledgeSource] = Field(
        default_factory=list
    )

    charts: list[WorkflowChartResponse] = Field(
        default_factory=list
    )

    execution_events: list[
        WorkflowExecutionEventResponse
    ] = Field(default_factory=list)
