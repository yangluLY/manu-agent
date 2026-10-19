
from typing import Any

from agent.workflow.schemas.response import (
    WorkflowChartResponse,
    WorkflowExecutionEventResponse,
    WorkflowResponse,
    WorkflowStepResponse,
)
from agent.workflow.schemas.result import KnowledgeSource
from agent.workflow.state import WorkflowState

FINAL_STATUSES = {
    "completed",
    "partial",
    "failed",
}


def build_workflow_response(
    state: WorkflowState,
) -> WorkflowResponse:
    """
    WorkflowState -> WorkflowResponse。

    支持：
    - completed
    - partial
    - failed
    """

    workflow_id = state.get("workflow_id")

    if not workflow_id:
        raise ValueError(
            "WorkflowState 缺少 workflow_id"
        )

    status = state.get("workflow_status")

    if status not in FINAL_STATUSES:
        raise ValueError(
            "只能转换已结束的工作流"
        )

    answer = state.get(
        "final_answer",
        "",
    )

    if not answer.strip():
        raise ValueError(
            "WorkflowState 缺少最终回答"
        )

    raw_steps = state.get(
        "step_results",
        [],
    )

    steps: list[WorkflowStepResponse] = []
    sources: list[KnowledgeSource] = []
    charts: list[WorkflowChartResponse] = []

    source_keys: set[tuple[int, int]] = set()

    for raw_step in raw_steps:
        step = WorkflowStepResponse.model_validate(
            raw_step
        )

        steps.append(step)

        # 失败步骤不参与来源和图表聚合
        if step.status != "success":
            continue

        for source in step.sources:
            key = (
                source.document_id,
                source.chunk_id,
            )

            if key in source_keys:
                continue

            source_keys.add(key)
            sources.append(source)

        if (
            step.agent == "bi"
            and step.chart is not None
        ):
            charts.append(
                WorkflowChartResponse(
                    step_id=step.step_id,
                    agent="bi",
                    option=step.chart,
                )
            )

    raw_events: list[dict[str, Any]] = (
        state.get("execution_events", [])
    )

    events = [
        WorkflowExecutionEventResponse.model_validate(
            event
        )
        for event in raw_events
    ]

    return WorkflowResponse(
        workflow_id=workflow_id,
        status=status,
        route=state["route"],
        route_reason=state.get(
            "route_reason",
            "",
        ),
        answer=answer,
        steps=steps,
        sources=sources,
        charts=charts,
        execution_events=events,
    )
