
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
    # 用户输入
    user_input: str

    # Router 状态
    route: RouteType
    route_reason: str

    # Planner 状态
    plan: list[PlanStep]
    current_step: int

    # 执行结果
    result: str

    # 最终回答
    final_answer: str
