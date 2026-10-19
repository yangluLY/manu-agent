
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

WorkflowStatus = Literal[
    "pending",
    "running",
    "completed",
    "partial",
    "failed",
]

ExecutionEventType = Literal[
    "workflow_started",
    "step_retry",
    "step_completed",
    "step_failed",
    "workflow_completed",
    "workflow_partial",
    "workflow_failed",
]


class ExecutionEvent(BaseModel):
    event_type: ExecutionEventType

    step_id: int | None = None
    agent: str | None = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    duration_ms: float | None = None

    details: dict[str, Any] = Field(
        default_factory=dict
    )
