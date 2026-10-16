from typing import Literal, TypedDict

from agent.workflow.schemas.plan import PlanStep

RouteType = Literal[
    "mes",
    "rag",
    "bi",
    "general",
    "complex",
]


class WorkflowState(TypedDict):
    user_input: str

    # Router
    route: RouteType
    route_reason: str

    # Planner
    plan: list[PlanStep]
    current_step: int

    # V4.4 执行记录
    step_results: list[dict]

    # 当前执行结果
    result: str

    # 最终回答
    final_answer: str