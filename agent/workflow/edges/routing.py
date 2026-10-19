
from typing import Literal

from agent.workflow.state import WorkflowState


def route_by_intent(
    state: WorkflowState,
) -> Literal[
    "mes",
    "rag",
    "bi",
    "general",
    "complex",
]:
    return state["route"]
