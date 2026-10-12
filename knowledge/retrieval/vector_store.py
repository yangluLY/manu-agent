from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.database.models.knowledge_chunk import KnowledgeChunk
from services.database.models.knowledge_document import KnowledgeDocument


@dataclass
class VectorSearchResult:
    chunk_id: int
    document_id: int
    document_name: str
    content: str
    chunk_index: int
    metadata: dict[str, Any] | None
    score: float


class VectorStore:

    def __init__(self, db: Session):
        self.db = db

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float | None = None,
        category: str | None = None,
        file_type: str | None = None,
        document_id: int | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:

        if not query_embedding:
            raise ValueError(
                "query_embedding cannot be empty"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0"
            )

        distance_expr = (
            KnowledgeChunk.embedding.cosine_distance(
                query_embedding
            )
        )

        distance = distance_expr.label(
            "distance"
        )

        stmt = (
            select(
                KnowledgeChunk,
                KnowledgeDocument,
                distance,
            )
            .join(
                KnowledgeDocument,
                KnowledgeChunk.document_id
                == KnowledgeDocument.id,
            )
            .where(
                KnowledgeChunk.embedding.is_not(None)
            )
        )

        # -----------------------------
        # Similarity Threshold
        # -----------------------------

        if min_score is not None:
            stmt = stmt.where(
                distance_expr <= 1.0 - min_score
            )

        # -----------------------------
        # Metadata / Document Filters
        # -----------------------------

        if category:
            stmt = stmt.where(
                KnowledgeDocument.category == category
            )

        if file_type:
            stmt = stmt.where(
                KnowledgeDocument.file_type == file_type
            )

        if document_id is not None:
            stmt = stmt.where(
                KnowledgeDocument.id == document_id
            )

        if metadata_filter:
            stmt = stmt.where(
                KnowledgeChunk.chunk_metadata.contains(
                    metadata_filter
                )
            )

        stmt = (
            stmt
            .order_by(distance_expr)
            .limit(top_k)
        )

        rows = self.db.execute(stmt).all()

        results: list[VectorSearchResult] = []

        for chunk, document, cosine_distance in rows:

            score = (
                1.0 - float(cosine_distance)
            )

            results.append(
                VectorSearchResult(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_name=document.name,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.chunk_metadata,
                    score=score,
                )
            )

        return results