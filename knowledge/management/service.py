from pathlib import Path

from sqlalchemy.orm import Session

from knowledge.ingestion.loaders import (
    DocumentLoader,
)
from knowledge.ingestion.pipeline import (
    IngestionPipeline,
)
from services.database.repositories.knowledge_repository import (
    KnowledgeRepository,
)


class KnowledgeManagementService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.repository = (
            KnowledgeRepository(db)
        )

        self.loader = DocumentLoader()

    def list_documents(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        category: str | None = None,
    ):
        return self.repository.list_documents(
            offset=offset,
            limit=limit,
            category=category,
        )

    def delete_document(
        self,
        document_id: int,
    ) -> bool:

        document = (
            self.repository.find_document_by_id(
                document_id
            )
        )

        if document is None:
            return False

        self.repository.delete_document(
            document
        )

        return True

    def reingest_document(
        self,
        document_id: int,
    ) -> int:

        document = (
            self.repository.find_document_by_id(
                document_id
            )
        )

        if document is None:
            raise LookupError(
                "Knowledge document not found"
            )

        path = Path(
            document.file_path
        )

        if not path.exists():
            raise FileNotFoundError(
                document.file_path
            )

        loaded_document = (
            self.loader.load_file(path)
        )

        pipeline = IngestionPipeline(
            db=self.db
        )

        return pipeline.ingest_document(
            loaded_document
        )

    def get_status(
        self,
    ) -> dict:

        return self.repository.get_status()