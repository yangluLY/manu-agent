from typing import Literal

from agent.workflow.state import WorkflowState


def should_continue(
    state: WorkflowState,
) -> Literal["continue", "finish"]:
    """
    判断是否还有未完成步骤。
    """

    current_step = state["current_step"]
    total_steps = len(state["plan"])

    if current_step < total_steps:
        return "continue"

    return "finish"