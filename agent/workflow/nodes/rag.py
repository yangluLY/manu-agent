
from agent.workflow.state import WorkflowState


def rag_node(state: WorkflowState) -> dict:
    return {
        "result": (
            f"[RAG Agent 模拟执行] "
            f"{state['user_input']}"
        )
    }
