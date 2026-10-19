
import json
from typing import Callable  # noqa: UP035

from agent.workflow.state import WorkflowState

ROUTES = {
    "mes",
    "rag",
    "bi",
    "general",
    "complex",
}


ROUTER_SYSTEM_PROMPT = """
你是 ManuAgent 智能制造系统的任务路由器。

请根据用户问题，判断最合适的任务类型。

可选类型：

1. mes
查询设备状态、设备信息、工单、库存、生产记录等业务数据。

2. rag
查询维修知识、操作规范、设备手册、故障处理文档。

3. bi
统计分析生产数据、故障趋势、产量、良品率、生成分析图表。

4. general
普通对话、问候，或者无法归类为制造业务任务的问题。

5. complex
需要组合多个不同能力完成的任务。
例如先查询故障数据，再统计分析，并结合维修文档提出建议。

分类原则：
- 根据用户的主要意图分类，而不是简单匹配关键词。
- 需要跨 MES、RAG、BI 多种能力时，选择 complex。
- 单纯的设备数据查询选择 mes。
- 单纯的知识文档查询选择 rag。
- 需要汇总、趋势分析、图表时选择 bi。

只能输出合法 JSON，不要输出 Markdown。

JSON 格式：
{
    "route": "mes",
    "reason": "用户希望查询设备实时状态"
}
"""


def parse_route(content: str) -> dict:
    data = json.loads(content)

    if not isinstance(data, dict):
        raise ValueError("Router 返回的不是 JSON 对象")  # noqa: TRY004

    route = data.get("route")
    reason = data.get("reason", "")

    if route not in ROUTES:
        raise ValueError(f"不支持的路由类型: {route}")

    if not isinstance(reason, str):
        raise ValueError("reason 必须为字符串")  # noqa: TRY004

    return {
        "route": route,
        "route_reason": reason,
    }


def create_router_node(
    llm_invoke: Callable[[str, str], str],
):
    """
    llm_invoke(system_prompt, user_input) -> str
    """

    def router_node(state: WorkflowState) -> dict:
        content = llm_invoke(
            ROUTER_SYSTEM_PROMPT,
            state["user_input"],
        )

        return parse_route(content)

    return router_node
