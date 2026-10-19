
from agent.workflow.schemas.execution import ExecutionEvent
from agent.workflow.state import WorkflowState


def approval_rejected_node(
    state: WorkflowState,
) -> dict:
    """
    审批拒绝后终止工作流。

    不调用任何业务 Agent。
    不伪造执行结果。
    """

    if state.get("approval_status") != "rejected":
        raise ValueError(
            "当前工作流并非审批拒绝状态"
        )

    event = ExecutionEvent(
        event_type="workflow_failed",
        details={
            "reason": "approval_rejected",
            "route": state["route"],
        },
    )

    return {
        "workflow_status": "failed",
        "final_answer": (
            "本次工作流未获得人工审批，"
            "已终止执行。未调用业务 Agent。"
        ),
        "step_results": [],
        "execution_events": [
            *state.get("execution_events", []),
            event.model_dump(mode="json"),
        ],
    }
