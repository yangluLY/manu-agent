
from agent.workflow.state import WorkflowState


def general_node(state: WorkflowState) -> dict:
    return {
        "result": (
            f"[General Agent 模拟执行] "
            f"{state['user_input']}"
        )
    }


def complex_node(state: WorkflowState) -> dict:
    return {
        "result": (
            "检测到复合任务，需要 Planner "
            "进行多步骤规划。该功能将在 V4.3 实现。"
        )
    }
