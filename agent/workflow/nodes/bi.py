
from agent.workflow.state import WorkflowState


def bi_node(state: WorkflowState) -> dict:
    return {
        "result": (
            f"[BI Agent 模拟执行] "
            f"{state['user_input']}"
        )
    }
