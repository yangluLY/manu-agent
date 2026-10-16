
from langgraph.graph import END, START, StateGraph

from agent.workflow.edges.execution import should_continue
from agent.workflow.edges.routing import route_by_intent
from agent.workflow.executors.mock import (
    mock_step_runner,
)
from agent.workflow.nodes.bi import bi_node
from agent.workflow.nodes.general import general_node
from agent.workflow.nodes.mes import mes_node
from agent.workflow.nodes.planner import (
    create_planner_node,
)
from agent.workflow.nodes.rag import rag_node
from agent.workflow.nodes.response import response_node
from agent.workflow.nodes.router import (
    create_router_node,
)
from agent.workflow.nodes.step_executor import (
    create_step_executor_node,
)
from agent.workflow.state import WorkflowState


def build_workflow(
    llm_invoke,
    step_runner=None,
):
    """
    构建 V4.4 LangGraph 工作流。
    """

    if step_runner is None:
        step_runner = mock_step_runner

    builder = StateGraph(WorkflowState)

    # 创建 LLM 节点
    router_node = create_router_node(llm_invoke)
    planner_node = create_planner_node(llm_invoke)

    # 创建步骤执行节点
    step_executor_node = create_step_executor_node(
        step_runner
    )

    # 注册节点
    builder.add_node("router", router_node)
    builder.add_node("planner", planner_node)
    builder.add_node(
        "step_executor",
        step_executor_node,
    )

    builder.add_node("mes", mes_node)
    builder.add_node("rag", rag_node)
    builder.add_node("bi", bi_node)
    builder.add_node("general", general_node)
    builder.add_node("response", response_node)

    # START
    builder.add_edge(START, "router")

    # Router 条件分支
    builder.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "mes": "mes",
            "rag": "rag",
            "bi": "bi",
            "general": "general",
            "complex": "planner",
        },
    )

    # 普通任务
    for node in [
        "mes",
        "rag",
        "bi",
        "general",
    ]:
        builder.add_edge(node, "response")

    # 复合任务：
    # Planner -> Step Executor
    builder.add_edge(
        "planner",
        "step_executor",
    )

    # 判断是否继续执行
    builder.add_conditional_edges(
        "step_executor",
        should_continue,
        {
            "continue": "step_executor",
            "finish": "response",
        },
    )

    # 结束
    builder.add_edge("response", END)

    return builder.compile()
