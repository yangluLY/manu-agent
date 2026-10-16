
from agent.workflow.schemas.plan import PlanStep
from agent.workflow.schemas.result import (
    AgentOutput,
    KnowledgeSource,
)
from knowledge.retrieval.retriever import KnowledgeRetriever


def create_rag_runner(
    retriever: KnowledgeRetriever,
):

    def run(
        step: PlanStep,
        previous_results: list[dict],
    ) -> AgentOutput:

        if step.agent != "rag":
            raise ValueError(
                "当前步骤不是 RAG 任务"
            )

        results = retriever.search(
            query=step.task,
            top_k=5,
        )

        if not results:
            return AgentOutput(
                output="未检索到符合条件的相关知识文档。",
                sources=[],
            )

        sources = [
            KnowledgeSource(
                document_id=item.document_id,
                document_name=item.document_name,
                chunk_id=item.chunk_id,
                chunk_index=item.chunk_index,
                score=item.score,
                content=item.content,
                metadata=item.metadata,
            )
            for item in results
        ]

        lines = []

        for source in sources:
            lines.append(
                f"文档：{source.document_name}\n"
                f"片段ID：{source.chunk_id}\n"
                f"内容：{source.content}"
            )

        return AgentOutput(
            output="\n\n".join(lines),
            sources=sources,
        )

    return run
