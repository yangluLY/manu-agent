from knowledge.retrieval.retriever import KnowledgeRetriever
from knowledge.retrieval.vector_store import VectorSearchResult


class FakeEmbedder:

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        return [0.1] * 512


class FakeVectorStore:

    def __init__(self):
        self.last_kwargs = None

    def similarity_search(
        self,
        **kwargs,
    ):
        self.last_kwargs = kwargs

        return [
            VectorSearchResult(
                chunk_id=1,
                document_id=1,
                document_name="cnc_alarm_manual",
                content=(
                    "主轴温度过高时应检查冷却液和冷却泵。"
                ),
                chunk_index=0,
                metadata={
                    "category": "alarm",
                },
                score=0.82,
            )
        ]


def test_retriever_search():

    vector_store = FakeVectorStore()

    retriever = KnowledgeRetriever(
        db=None,
        embedder=FakeEmbedder(),
        vector_store=vector_store,
    )

    results = retriever.search(
        query="主轴温度过高怎么办？",
        top_k=3,
        min_score=0.5,
        category="alarm",
    )

    assert len(results) == 1
    assert results[0].document_name == "cnc_alarm_manual"
    assert results[0].score == 0.82

    assert vector_store.last_kwargs["top_k"] == 3
    assert vector_store.last_kwargs["min_score"] == 0.5
    assert vector_store.last_kwargs["category"] == "alarm"

import pytest


def test_retriever_rejects_empty_query():

    retriever = KnowledgeRetriever(
        db=None,
        embedder=FakeEmbedder(),
        vector_store=FakeVectorStore(),
    )

    with pytest.raises(ValueError):
        retriever.search("   ")