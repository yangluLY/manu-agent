from agent.workflow.state import WorkflowState


def executor_node(state: WorkflowState) -> dict:
    route = state["route"]

    results = {
        "mes": "MES Agent 执行成功",
        "rag": "RAG Agent 执行成功",
        "bi": "BI Agent 执行成功",
        "general": "通用问题处理成功",
    }

    return {
        "result": results.get(route, "未知任务类型")
    }