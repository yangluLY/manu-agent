
from typing import Literal

from agent.workflow.state import WorkflowState

ExecutionDecision = Literal[
    "continue",
    "finish",
    "failed",
]


def should_continue(
    state: WorkflowState,
) -> ExecutionDecision:
    """
    控制 Step Executor 循环。

    任何步骤失败，都停止后续步骤。
    """

    results = state.get(
        "step_results",
        [],
    )

    if not results:
        raise ValueError(
            "Step Executor 没有执行结果"
        )

    last_result = results[-1]

    if last_result["status"] == "failed":
        return "failed"

    if state["current_step"] < len(state["plan"]):
        return "continue"

    return "finish"
