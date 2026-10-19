
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CheckpointStatus = Literal[
    "unknown",
    "pending",
    "running",
    "completed",
    "partial",
    "failed",
]


class CheckpointSummary(BaseModel):
    """单个检查点的摘要。"""

    thread_id: str
    checkpoint_id: str

    parent_checkpoint_id: str | None = None

    created_at: datetime | None = None

    source: str | None = None
    step: int | None = None

    next_nodes: list[str] = Field(
        default_factory=list
    )

    workflow_id: str | None = None

    workflow_status: CheckpointStatus = "unknown"

    route: str | None = None

    completed_steps: int = 0


class WorkflowHistoryResponse(BaseModel):
    """工作流历史列表。"""

    thread_id: str

    total: int

    checkpoints: list[CheckpointSummary] = Field(
        default_factory=list
    )


class WorkflowStateDetail(BaseModel):
    """指定检查点的业务状态详情。"""

    checkpoint: CheckpointSummary

    final_answer: str | None = None

    executed_steps: list[dict] = Field(
        default_factory=list
    )

    execution_events: list[dict] = Field(
        default_factory=list
    )
