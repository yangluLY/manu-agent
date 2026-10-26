
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from services.database.base import Base

if TYPE_CHECKING:
    from services.database.models.knowledge_document import (
        KnowledgeDocument,
    )


EMBEDDING_DIM = 512


class KnowledgeChunk(Base):
    """
    知识库文档切片。

    PostgreSQL:
        metadata -> JSONB
        embedding -> vector(512)

    SQLite 测试:
        metadata -> JSON
        embedding -> JSON

    注意：
        SQLite 仅用于普通数据操作测试，
        不支持 PostgreSQL pgvector 相似度检索。
    """

    __tablename__ = "knowledge_chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_knowledge_chunk_document_index",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "knowledge_documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # PostgreSQL JSONB / SQLite JSON
    chunk_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB().with_variant(
            JSON(),
            "sqlite",
        ),
        nullable=True,
    )

    # PostgreSQL pgvector / SQLite JSON
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM).with_variant(
            JSON(),
            "sqlite",
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    document: Mapped["KnowledgeDocument"] = relationship(
        back_populates="chunks",
    )
