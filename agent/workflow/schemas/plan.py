
from typing import Literal

from pydantic import BaseModel, Field, model_validator

AgentType = Literal[
    "mes",
    "rag",
    "bi",
    "summary",
]


class PlanStep(BaseModel):
    id: int = Field(ge=1)

    agent: AgentType

    task: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_task(self):
        if not self.task.strip():
            raise ValueError("任务内容不能为空")
        return self


class ExecutionPlan(BaseModel):
    """
    Planner 输出的结构化任务计划。
    """

    steps: list[PlanStep] = Field(
        min_length=1,
        max_length=8,
    )

    @model_validator(mode="after")
    def validate_steps(self):
        ids = [step.id for step in self.steps]

        expected = list(range(1, len(ids) + 1))

        if ids != expected:
            raise ValueError(
                "步骤 ID 必须从 1 开始连续递增"
            )

        if self.steps[-1].agent != "summary":
            raise ValueError(
                "最后一步必须是 summary"
            )

        if any(
            step.agent == "summary"
            for step in self.steps[:-1]
        ):
            raise ValueError(
                "summary 只能作为最后一步"
            )

        if not any(
            step.agent in ("mes", "rag", "bi")
            for step in self.steps[:-1]
        ):
            raise ValueError(
                "计划至少需要一个业务执行步骤"
            )

        return self
