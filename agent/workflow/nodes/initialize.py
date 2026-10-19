from uuid import uuid4

from agent.workflow.schemas.execution import (
    ExecutionEvent,
)
from agent.workflow.state import WorkflowState


def initialize_node(state: WorkflowState) -> dict:
    """
    初始化本次工作流执行状态。
    """

    workflow_id = str(uuid4())

    event = ExecutionEvent(
        event_type="workflow_started",
        details={
            "user_input": state["user_input"],
        },
    )

    return {
        "workflow_id": workflow_id,
        "workflow_status": "running",
        "execution_events": [
            event.model_dump(mode="json")
        ],
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }