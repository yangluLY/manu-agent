
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeSource(BaseModel):
    """RAG 知识引用来源。"""

    document_id: int
    document_name: str

    chunk_id: int
    chunk_index: int

    score: float

    content: str

    metadata: dict[str, Any] | None = None


class AgentOutput(BaseModel):
    """
    各业务 Agent 的统一结构化输出。

    output: 给用户或下游 Agent 阅读的文本
    data: 结构化业务数据
    sources: 知识库引用
    sql: BI 执行的 SQL
    chart: ECharts option
    """

    output: str = Field(min_length=1)

    data: dict[str, Any] | None = None

    sources: list[KnowledgeSource] = Field(
        default_factory=list,
    )

    sql: str | None = None

    chart: dict[str, Any] | None = None
