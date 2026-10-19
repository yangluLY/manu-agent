
from langgraph.types import interrupt

from agent.workflow.state import WorkflowState


def approval_gate_node(
    state: WorkflowState,
) -> dict:
    """
    人工审批节点。

    在 Step Executor 执行前暂停，
    等待外部通过 Command(resume=...) 提交决定。

    注意：
    interrupt() 之前不能进行写数据库、
    创建工单等有副作用的操作。
    """

    workflow_id = state.get("workflow_id")

    if not workflow_id:
        raise ValueError(
            "审批节点缺少 workflow_id"
        )

    plan = state.get("plan", [])

    if not plan:
        raise ValueError(
            "审批节点缺少执行计划"
        )

    # 只向审批方展示必要的计划信息
    payload = {
        "type": "workflow_approval",
        "workflow_id": workflow_id,
        "route": state["route"],
        "step_count": len(plan),
        "agents": [
            step.agent
            for step in plan
        ],
        "message": (
            "是否允许执行本次只读分析工作流？"
        ),
    }

    # 首次调用：暂停工作流
    # 恢复调用：返回 Command(resume=...) 的内容
    decision = interrupt(payload)

    if not isinstance(decision, dict):
        raise ValueError(  # noqa: TRY004
            "审批结果必须是字典"
        )

    # 必须匹配当前工作流
    if decision.get("workflow_id") != workflow_id:
        raise ValueError(
            "审批 workflow_id 不匹配"
        )

    approved = decision.get("approved")

    # 防止字符串 "false" 被错误识别为 True
    if type(approved) is not bool:
        raise ValueError(
            "approved 必须是布尔值"
        )

    return {
        "approval_status": (
            "approved"
            if approved
            else "rejected"
        )
    }


def route_after_approval(
    state: WorkflowState,
) -> str:
    """
    审批后条件路由。
    """

    status = state.get(
        "approval_status"
    )

    if status == "approved":
        return "approved"

    if status == "rejected":
        return "rejected"

    raise ValueError(
        "审批结果尚未确定"
    )
