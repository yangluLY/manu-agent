from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.database.base import Base

if TYPE_CHECKING:
    from services.database.models.knowledge_chunk import KnowledgeChunk


class KnowledgeDocument(Base):
    """
    知识库原始文档

    一条记录代表一份被导入知识库的原始文档，
    例如设备说明书、报警手册、维修 SOP 等。
    """

    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="internal",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )