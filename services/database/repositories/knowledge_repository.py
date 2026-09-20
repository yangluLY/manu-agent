from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from services.database.models.knowledge_chunk import KnowledgeChunk
from services.database.models.knowledge_document import KnowledgeDocument


class KnowledgeRepository:
    """
    知识库数据库访问层。

    负责：
    - 创建/更新知识文档
    - 创建知识 Chunk
    - 删除旧 Chunk
    - 根据文件路径查询文档
    """

    def __init__(self, db: Session):
        self.db = db

    def find_document_by_path(
        self,
        file_path: str,
    ) -> KnowledgeDocument | None:
        """
        根据文件路径查询知识文档。
        """

        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.file_path == file_path
        )

        return self.db.scalar(stmt)

    def create_document(
        self,
        *,
        name: str,
        file_path: str,
        file_type: str,
        category: str | None = None,
        source: str = "internal",
    ) -> KnowledgeDocument:
        """
        创建知识文档记录。
        """

        document = KnowledgeDocument(
            name=name,
            file_path=file_path,
            file_type=file_type,
            category=category,
            source=source,
        )

        self.db.add(document)

        # flush 后可以拿到 document.id，
        # 但事务暂时还没有 commit。
        self.db.flush()

        return document

    def update_document(
        self,
        document: KnowledgeDocument,
        *,
        name: str,
        file_type: str,
        category: str | None,
        source: str = "internal",
    ) -> KnowledgeDocument:
        """
        更新已经存在的知识文档。
        """

        document.name = name
        document.file_type = file_type
        document.category = category
        document.source = source

        self.db.flush()

        return document

    def delete_chunks_by_document_id(
        self,
        document_id: int,
    ) -> None:
        """
        删除某个文档已有的所有 Chunk。

        重新导入文档时会使用。
        """

        stmt = delete(KnowledgeChunk).where(
            KnowledgeChunk.document_id == document_id
        )

        self.db.execute(stmt)
        self.db.flush()

    def create_chunk(
        self,
        *,
        document_id: int,
        content: str,
        chunk_index: int,
        metadata: dict | None,
        embedding: list[float],
    ) -> KnowledgeChunk:
        """
        创建单个知识 Chunk。
        """

        chunk = KnowledgeChunk(
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            chunk_metadata=metadata,
            embedding=embedding,
        )

        self.db.add(chunk)

        return chunk

    def create_chunks(
        self,
        *,
        document_id: int,
        chunks: list[dict],
    ) -> list[KnowledgeChunk]:
        """
        批量创建 Chunk。

        chunks 中每个元素结构：

        {
            "content": "...",
            "chunk_index": 0,
            "metadata": {...},
            "embedding": [...]
        }
        """

        entities: list[KnowledgeChunk] = []

        for item in chunks:
            entity = KnowledgeChunk(
                document_id=document_id,
                content=item["content"],
                chunk_index=item["chunk_index"],
                chunk_metadata=item.get("metadata"),
                embedding=item["embedding"],
            )

            entities.append(entity)

        self.db.add_all(entities)

        return entities

    def find_document_by_id(
        self,
        document_id: int,
    ) -> KnowledgeDocument | None:
        return self.db.get(
            KnowledgeDocument,
            document_id,
        )


    def list_documents(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        category: str | None = None,
    ) -> list[KnowledgeDocument]:

        stmt = select(
            KnowledgeDocument
        )

        if category:
            stmt = stmt.where(
                KnowledgeDocument.category
                == category
            )

        stmt = (
            stmt
            .order_by(
                KnowledgeDocument.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt).all()
        )


    def delete_document(
        self,
        document: KnowledgeDocument,
    ) -> None:

        self.db.delete(document)
        self.db.commit()


    def get_status(
        self,
    ) -> dict:

        document_count = self.db.scalar(
            select(
                func.count(KnowledgeDocument.id)
            )
        ) or 0

        chunk_count = self.db.scalar(
            select(
                func.count(KnowledgeChunk.id)
            )
        ) or 0

        embedded_count = self.db.scalar(
            select(
                func.count(KnowledgeChunk.id)
            ).where(
                KnowledgeChunk.embedding.is_not(None)
            )
        ) or 0

        category_rows = self.db.execute(
            select(
                KnowledgeDocument.category,
                func.count(
                    KnowledgeDocument.id
                ),
            )
            .group_by(
                KnowledgeDocument.category
            )
        ).all()

        categories = {
            category or "uncategorized": count
            for category, count in category_rows
        }

        return {
            "documents": document_count,
            "chunks": chunk_count,
            "embedded_chunks": embedded_count,
            "categories": categories,
        }