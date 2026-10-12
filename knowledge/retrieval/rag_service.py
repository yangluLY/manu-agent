from dataclasses import dataclass

from sqlalchemy.orm import Session

from agent.llm.deepseek_client import DeepSeekClient
from knowledge.retrieval.retriever import KnowledgeRetriever
from knowledge.retrieval.vector_store import VectorSearchResult


@dataclass
class RAGAnswer:
    """
    RAG 最终回答结果。
    """

    answer: str
    sources: list[VectorSearchResult]


class RAGService:
    """
    ManuAgent 企业知识库 RAG Service。

    流程：

    用户问题
       ↓
    Retriever
       ↓
    Top K Knowledge Chunks
       ↓
    构造 RAG Context
       ↓
    DeepSeek
       ↓
    最终回答
    """

    def __init__(
        self,
        db: Session,
        retriever: KnowledgeRetriever | None = None,
        llm: DeepSeekClient | None = None,
    ):
        self.retriever = (
            retriever
            or KnowledgeRetriever(db)
        )

        self.llm = (
            llm
            or DeepSeekClient()
        )

    def query(
        self,
        question: str,
        top_k: int | None = None,
        min_score: float | None = None,
        category: str | None = None,
    ) -> RAGAnswer:
        """
        根据企业知识库回答用户问题。
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "question cannot be empty"
            )

        # 1. 检索相关知识
        results = self.retriever.search(
            query=question,
            top_k=top_k,
            min_score=min_score,
            category=category,
        )

        if not results:
            return RAGAnswer(
                answer=(
                    "当前企业知识库中没有检索到"
                    "足够相关的资料，暂时无法根据知识库"
                    "可靠回答该问题。"
                ),
                sources=[],
            )

        # 2. 构造知识上下文
        context = self._build_context(
            results
        )

        # 3. 构造 system instructions
        instructions = self._build_instructions()

        # 4. 构造用户输入
        input_items = self._build_input(
            question=question,
            context=context,
        )

        # 5. 调用 DeepSeek
        answer = self._call_llm(
            instructions=instructions,
            input_items=input_items,
        )

        return RAGAnswer(
            answer=answer,
            sources=results,
        )

    @staticmethod
    def _build_context(
        results: list[VectorSearchResult],
    ) -> str:
        """
        将 Retriever 返回的多个 Chunk
        组合成提供给 LLM 的 Context。
        """

        context_parts: list[str] = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            context_parts.append(
                (
                    f"[知识 {index}]\n"
                    f"文档：{result.document_name}\n"
                    f"Chunk：{result.chunk_index}\n"
                    f"内容：\n"
                    f"{result.content}"
                )
            )

        return "\n\n".join(
            context_parts
        )

    @staticmethod
    def _build_instructions() -> str:
        """
        RAG system prompt。
        """

        return """
你是 ManuAgent 智能制造生产运营助手。

你的任务是根据提供的企业知识库资料回答用户问题。

回答要求：

1. 优先且严格依据企业知识库中的内容回答。
2. 不要编造知识库中不存在的设备参数、报警代码、维修步骤或安全阈值。
3. 如果知识库资料不足以回答问题，应明确说明资料不足。
4. 回答应清晰、专业，并尽量给出可执行的处理步骤。
5. 如果多个知识片段存在关联，可以综合整理后回答。
6. 不要把检索到的资料描述成你自身掌握的事实，应以企业知识库内容为依据。
""".strip()

    @staticmethod
    def _build_input(
        question: str,
        context: str,
    ) -> list[dict[str, str]]:
        """
        构造 Responses API input。
        """

        user_content = f"""
以下是从企业知识库中检索到的相关资料：

{context}

用户问题：

{question}

请根据以上企业知识库资料回答用户问题。
""".strip()

        return [
            {
                "role": "user",
                "content": user_content,
            }
        ]

    def _call_llm(
        self,
        *,
        instructions: str,
        input_items: list[dict[str, str]],
    ) -> str:
        """
        调用 V1 已有的 DeepSeekClient。
        """

        response = self.llm.create_response(
            input_items=input_items,
            instructions=instructions,
            tools=None,
        )

        return self._extract_text(
            response
        )

    @staticmethod
    def _extract_text(response) -> str:
        """
        从 Responses API 返回结果中提取文本。
        """

        output_text = getattr(
            response,
            "output_text",
            None,
        )

        if output_text:
            return output_text.strip()

        # fallback:
        # 防止兼容 API 没有提供 output_text 快捷属性
        texts: list[str] = []

        for item in getattr(
            response,
            "output",
            [],
        ):
            for content in getattr(
                item,
                "content",
                [],
            ):
                text = getattr(
                    content,
                    "text",
                    None,
                )

                if text:
                    texts.append(text)

        answer = "\n".join(texts).strip()

        if not answer:
            raise RuntimeError(
                "DeepSeek returned no text response"
            )

        return answer