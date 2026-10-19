
from agent.workflow.schemas.plan import PlanStep
from agent.workflow.state import WorkflowState

SIMPLE_ROUTES = {
    "mes",
    "rag",
    "bi",
}


def simple_planner_node(
    state: WorkflowState,
) -> dict:
    """
    将普通 MES / RAG / BI 请求
    转换为单步骤执行计划。

    不调用 LLM。
    """

    route = state["route"]

    if route not in SIMPLE_ROUTES:
        raise ValueError(
            f"Simple Planner 不支持路由: {route}"
        )

    user_input = state["user_input"].strip()

    if not user_input:
        raise ValueError(
            "用户输入不能为空"
        )

    step = PlanStep(
        id=1,
        agent=route,
        task=user_input,
    )

    return {
        "plan": [step],
        "current_step": 0,
        "step_results": [],
        "result": "",
    }
