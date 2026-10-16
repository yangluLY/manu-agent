
from langgraph.graph import END, START, StateGraph

from agent.workflow.edges.routing import route_by_intent
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
from agent.workflow.state import WorkflowState


def build_workflow(llm_invoke):
    builder = StateGraph(WorkflowState)

    # 1. 创建 LLM 节点
    router_node = create_router_node(llm_invoke)
    planner_node = create_planner_node(llm_invoke)

    # 2. 注册节点
    builder.add_node("router", router_node)
    builder.add_node("planner", planner_node)

    builder.add_node("mes", mes_node)
    builder.add_node("rag", rag_node)
    builder.add_node("bi", bi_node)
    builder.add_node("general", general_node)

    builder.add_node("response", response_node)

    # 3. START -> Router
    builder.add_edge(START, "router")

    # 4. Conditional Edge
    builder.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "mes": "mes",
            "rag": "rag",
            "bi": "bi",
            "general": "general",

            # 复合任务进入 Planner
            "complex": "planner",
        },
    )

    # 5. 普通任务直接进入 Response
    for node in [
        "mes",
        "rag",
        "bi",
        "general",
    ]:
        builder.add_edge(node, "response")

    # 6. 复合任务：Planner -> Response
    builder.add_edge("planner", "response")

    # 7. 结束
    builder.add_edge("response", END)

    return builder.compile()
