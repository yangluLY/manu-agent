
from typing import Literal, NotRequired, TypedDict

from agent.workflow.schemas.plan import PlanStep

RouteType = Literal[
    "mes",
    "rag",
    "bi",
    "general",
    "complex",
]

ApprovalStatus = Literal[
    "not_required",
    "approved",
    "rejected",
]


class WorkflowState(TypedDict):
    # 用户问题
    user_input: str

    # Router
    route: RouteType
    route_reason: str

    # Planner
    plan: list[PlanStep]
    current_step: int

    # Executor
    step_results: list[dict]
    result: str

    # Response
    final_answer: str

    # V4.5.1 新增
    workflow_id: NotRequired[str]
    workflow_status: NotRequired[str]
    execution_events: NotRequired[list[dict]]


    # V4.7.3 人工审批
    approval_status: NotRequired[ApprovalStatus]
