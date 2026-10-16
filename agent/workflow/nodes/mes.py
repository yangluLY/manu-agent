
from agent.workflow.state import WorkflowState


def mes_node(state: WorkflowState) -> dict:
    return {
        "result": (
            f"[MES Agent 模拟执行] "
            f"{state['user_input']}"
        )
    }
