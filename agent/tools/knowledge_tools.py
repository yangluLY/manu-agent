from agent.tools.serializers import (
    serialize_knowledge_search_result,
)
from agent.tools.types import ToolResult
from knowledge.retrieval.retriever import (
    KnowledgeRetriever,
)


class KnowledgeTools:
    """
    企业知识库查询工具。

    职责：
    - 接收 Agent 的自然语言知识检索请求
    - 调用 KnowledgeRetriever
    - 返回相关知识 Chunk
    - 不负责调用 LLM
    - 不负责生成最终自然语言回答
    """

    def __init__(
        self,
        retriever: KnowledgeRetriever,
    ):
        self.retriever = retriever

    def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> ToolResult:
        """
        搜索企业知识库。

        可用于：
        - 设备故障原因
        - 报警处理方法
        - 维修 SOP
        - 设备操作规范
        - 生产 SOP
        - 质量规范
        """

        normalized_query = query.strip()

        if not normalized_query:
            return ToolResult.fail(
                code="INVALID_KNOWLEDGE_QUERY",
                message="Knowledge query cannot be empty",
            )

        results = self.retriever.search(
            query=normalized_query,
            top_k=top_k,
            category=category,
        )

        # 没找到相关知识并不是 Tool 执行失败。
        # Retriever 正常工作，只是当前知识库没有可靠结果。
        if not results:
            return ToolResult.ok(
                {
                    "query": normalized_query,
                    "category": category,
                    "count": 0,
                    "results": [],
                    "message": (
                        "No sufficiently relevant "
                        "knowledge was found."
                    ),
                }
            )

        return ToolResult.ok(
            {
                "query": normalized_query,
                "category": category,
                "count": len(results),
                "results": [
                    serialize_knowledge_search_result(
                        result
                    )
                    for result in results
                ],
            }
        )