from pathlib import Path

from sqlalchemy.orm import Session

from knowledge.ingestion.embedder import Embedder
from knowledge.ingestion.loaders import DocumentLoader, LoadedDocument
from knowledge.ingestion.splitter import TextSplitter
from services.database.repositories.knowledge_repository import (
    KnowledgeRepository,
)


class IngestionPipeline:
    """
    知识库导入 Pipeline。

    完整流程：

    File
      ↓
    Loader
      ↓
    Splitter
      ↓
    Embedder
      ↓
    Repository
      ↓
    PostgreSQL
    """

    def __init__(
        self,
        db: Session,
        loader: DocumentLoader | None = None,
        splitter: TextSplitter | None = None,
        embedder: Embedder | None = None,
    ):
        self.db = db

        self.loader = loader or DocumentLoader()

        self.splitter = splitter or TextSplitter(
            chunk_size=500,
            chunk_overlap=100,
        )

        self.embedder = embedder or Embedder()

        self.repository = KnowledgeRepository(db)

    def ingest_directory(
        self,
        directory: str | Path,
    ) -> dict:
        """
        导入整个知识目录。
        """

        documents = self.loader.load_directory(
            directory
        )

        total_documents = 0
        total_chunks = 0
        failed_documents: list[dict] = []

        for document in documents:
            try:
                chunk_count = self.ingest_document(
                    document
                )

                total_documents += 1
                total_chunks += chunk_count

            except Exception as exc:
                self.db.rollback()

                failed_documents.append(
                    {
                        "file_name": document.metadata.get(
                            "file_name"
                        ),
                        "error": str(exc),
                    }
                )

                print(
                    f"[FAILED] "
                    f"{document.metadata.get('file_name')}: "
                    f"{exc}"
                )

        return {
            "documents": total_documents,
            "chunks": total_chunks,
            "failed": failed_documents,
        }

    def ingest_document(
        self,
        document: LoadedDocument,
    ) -> int:
        """
        导入单个文档。
        """

        file_path = document.metadata["source"]
        file_name = document.metadata["file_name"]
        file_type = document.metadata["file_type"]
        category = document.metadata.get("category")

        print()
        print(f"Processing: {file_name}")

        # -----------------------------------
        # 1. 文本切分
        # -----------------------------------

        chunks = self.splitter.split_document(
            document
        )

        if not chunks:
            raise ValueError(
                f"No content chunks generated: {file_name}"
            )

        print(
            f"Chunks created: {len(chunks)}"
        )

        # -----------------------------------
        # 2. 批量生成 embedding
        # -----------------------------------

        texts = [
            chunk.content
            for chunk in chunks
        ]

        embeddings = self.embedder.embed_documents(
            texts
        )

        if len(chunks) != len(embeddings):
            raise RuntimeError(
                "Chunk count and embedding count mismatch"
            )

        print(
            f"Embeddings generated: "
            f"{len(embeddings)}"
        )

        # -----------------------------------
        # 3. 查询文档是否已经存在
        # -----------------------------------

        db_document = (
            self.repository.find_document_by_path(
                file_path
            )
        )

        if db_document is None:
            db_document = (
                self.repository.create_document(
                    name=Path(file_name).stem,
                    file_path=file_path,
                    file_type=file_type,
                    category=category,
                    source="internal",
                )
            )

            print(
                f"Document created: "
                f"id={db_document.id}"
            )

        else:
            self.repository.update_document(
                db_document,
                name=Path(file_name).stem,
                file_type=file_type,
                category=category,
                source="internal",
            )

            self.repository.delete_chunks_by_document_id(
                db_document.id
            )

            print(
                f"Document updated: "
                f"id={db_document.id}"
            )

        # -----------------------------------
        # 4. 组织数据库 Chunk
        # -----------------------------------

        chunk_records: list[dict] = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            chunk_records.append(
                {
                    "content": chunk.content,
                    "chunk_index": chunk.metadata[
                        "chunk_index"
                    ],
                    "metadata": chunk.metadata,
                    "embedding": embedding,
                }
            )

        # -----------------------------------
        # 5. 写入数据库
        # -----------------------------------

        self.repository.create_chunks(
            document_id=db_document.id,
            chunks=chunk_records,
        )

        # -----------------------------------
        # 6. 当前文档事务提交
        # -----------------------------------

        self.db.commit()

        print(
            f"Inserted chunks: "
            f"{len(chunk_records)}"
        )

        return len(chunk_records)