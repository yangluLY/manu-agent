
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from agent.workflow.edges.execution import (
    should_continue,
)
from agent.workflow.edges.routing import (
    route_by_intent,
)
from agent.workflow.executors.mock import (
    mock_step_runner,
)
from agent.workflow.executors.retry_policy import RetryPolicy
from agent.workflow.nodes.approval import (
    approval_gate_node,
    route_after_approval,
)
from agent.workflow.nodes.approval_rejected import (
    approval_rejected_node,
)
from agent.workflow.nodes.general import (
    general_node,
)
from agent.workflow.nodes.initialize import (
    initialize_node,
)
from agent.workflow.nodes.planner import (
    create_planner_node,
)
from agent.workflow.nodes.response import (
    response_node,
)
from agent.workflow.nodes.router import (
    create_router_node,
)
from agent.workflow.nodes.simple_planner import (
    simple_planner_node,
)
from agent.workflow.nodes.step_executor import (
    create_step_executor_node,
)
from agent.workflow.state import WorkflowState


def build_workflow(
    llm_invoke,
    step_runner=None,
    retry_policy: RetryPolicy | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    require_approval: bool = False,
):
    """
    ManuAgent V4.5.2 统一工作流。

    mes/rag/bi -> Simple Planner
    complex -> LLM Planner
    general -> General Node

    所有路由统一输出 step_results。
    """

    if step_runner is None:
        step_runner = mock_step_runner

    if require_approval and checkpointer is None:
        raise ValueError(
            "人工审批功能必须配置 Checkpointer"
        )

        
    builder = StateGraph(WorkflowState)

    # 所有模式下都需要注册的节点
    builder.add_node("initialize", initialize_node)
    builder.add_node("router", create_router_node(llm_invoke))
    builder.add_node("simple_planner", simple_planner_node)
    builder.add_node("planner", create_planner_node(llm_invoke))

    builder.add_node(
        "step_executor",
        create_step_executor_node(
            step_runner,
            retry_policy=retry_policy,
        ),
    )

    builder.add_node("general", general_node)
    builder.add_node("response", response_node)

    # 只有审批模式才需要的节点
    if require_approval:
        builder.add_node("approval_gate", approval_gate_node)
        builder.add_node(
            "approval_rejected",
            approval_rejected_node,
        )


    
    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "router")

    builder.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "mes": "simple_planner",
            "rag": "simple_planner",
            "bi": "simple_planner",
            "general": "general",
            "complex": "planner",
        },
    )

    if require_approval:
        builder.add_edge(
            "simple_planner",
            "approval_gate",
        )

        builder.add_edge(
            "planner",
            "approval_gate",
        )

        builder.add_conditional_edges(
            "approval_gate",
            route_after_approval,
            {
                "approved": "step_executor",
                "rejected": "approval_rejected",
            },
        )

        builder.add_edge("approval_rejected", END)

    else:
        builder.add_edge(
            "simple_planner",
            "step_executor",
        )

        builder.add_edge(
            "planner",
            "step_executor",
        )

    builder.add_conditional_edges(
        "step_executor",
        should_continue,
        {
            "continue": "step_executor",
            "finish": "response",
            "failed": "response",
        },
    )

    builder.add_edge("general", "response")
    builder.add_edge("response", END)

    return builder.compile(checkpointer=checkpointer)
