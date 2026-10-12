from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from apps.api.app.schemas.knowledge import (
    KnowledgeDocumentResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeReingestResponse,
    KnowledgeSourceResponse,
    KnowledgeStatusResponse,
)
from knowledge.management.service import (
    KnowledgeManagementService,
)
from knowledge.retrieval.rag_service import RAGService
from services.database.session import get_db

router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
)


@router.post(
    "/query",
    response_model=KnowledgeQueryResponse,
)
def query_knowledge(
    payload: KnowledgeQueryRequest,
    db: Session = Depends(get_db),
) -> KnowledgeQueryResponse:
    rag_service = RAGService(db)

    result = rag_service.query(
        question=payload.question,
        top_k=payload.top_k,
        category=payload.category,
    )

    sources = [
        KnowledgeSourceResponse(
            chunk_id=source.chunk_id,
            document_id=source.document_id,
            document_name=source.document_name,
            chunk_index=source.chunk_index,
            score=source.score,
            content=source.content,
        )
        for source in result.sources
    ]

    return KnowledgeQueryResponse(
        answer=result.answer,
        sources=sources,
    )

@router.get(
    "/documents",
    response_model=list[
        KnowledgeDocumentResponse
    ],
)
def list_documents(
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    service = KnowledgeManagementService(
        db
    )

    return service.list_documents(
        offset=offset,
        limit=limit,
        category=category,
    )

@router.post(
    "/documents/{document_id}/reingest",
    response_model=KnowledgeReingestResponse,
)
def reingest_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    service = KnowledgeManagementService(
        db
    )

    try:
        chunks = service.reingest_document(
            document_id
        )

    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found",
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=409,
            detail=(
                "Knowledge source file "
                "does not exist"
            ),
        )

    return KnowledgeReingestResponse(
        document_id=document_id,
        chunks=chunks,
        message="Knowledge document reingested",
    )

@router.get(
    "/status",
    response_model=KnowledgeStatusResponse,
)
def knowledge_status(
    db: Session = Depends(get_db),
):
    service = KnowledgeManagementService(
        db
    )

    return service.get_status()

