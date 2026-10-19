from time import perf_counter

from agent.workflow.schemas.execution import ExecutionEvent
from agent.workflow.schemas.result import AgentOutput
from agent.workflow.state import WorkflowState


def general_node(state: WorkflowState) -> dict:
    """
    处理普通问候。

    V4.5.2 暂不调用业务 Agent，
    但返回统一结构化执行记录。
    """

    start = perf_counter()

    question = state["user_input"]

    answer = (
        "[General Agent 模拟执行] "
        f"{question}"
    )

    output = AgentOutput(
        output=answer,
    )

    duration_ms = round(
        (perf_counter() - start) * 1000,
        2,
    )

    step_result = {
        "step_id": 1,
        "agent": "general",
        "task": question,
        "status": "success",
        "duration_ms": duration_ms,
        **output.model_dump(mode="json"),
    }

    event = ExecutionEvent(
        event_type="step_completed",
        step_id=1,
        agent="general",
        duration_ms=duration_ms,
        details={"status": "success"},
    )

    return {
        "plan": [],
        "current_step": 0,
        "step_results": [step_result],
        "execution_events": [
            *state.get("execution_events", []),
            event.model_dump(mode="json"),
        ],
        "result": output.output,
    }


def complex_node(state: WorkflowState) -> dict:
    return {
        "result": (
            "检测到复合任务，需要 Planner "
            "进行多步骤规划。该功能将在 V4.3 实现。"
        )
    }
