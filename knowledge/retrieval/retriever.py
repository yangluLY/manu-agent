from typing import Any

from sqlalchemy.orm import Session

from knowledge.ingestion.embedder import Embedder
from knowledge.retrieval.config import retrieval_config
from knowledge.retrieval.vector_store import (
    VectorSearchResult,
    VectorStore,
)


class KnowledgeRetriever:

    def __init__(
        self,
        db: Session,
        embedder: Embedder | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.embedder = embedder or Embedder()

        self.vector_store = (
            vector_store
            or VectorStore(db)
        )

    def search(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
        category: str | None = None,
        file_type: str | None = None,
        document_id: int | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:

        query = query.strip()

        if not query:
            raise ValueError(
                "query cannot be empty"
            )

        config = retrieval_config

        if top_k is None:
            top_k = config.default_top_k

        top_k = min(
            top_k,
            config.max_top_k,
        )

        if min_score is None:
            min_score = config.min_score

        query_embedding = (
            self.embedder.embed_query(query)
        )

        return self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            min_score=min_score,
            category=category,
            file_type=file_type,
            document_id=document_id,
            metadata_filter=metadata_filter,
        )