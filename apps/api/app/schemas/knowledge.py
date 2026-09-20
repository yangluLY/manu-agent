from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description="用户知识库问题",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    category: str | None = None


class KnowledgeSourceResponse(BaseModel):
    chunk_id: int
    document_id: int
    document_name: str
    chunk_index: int
    score: float
    content: str


class KnowledgeQueryResponse(BaseModel):
    answer: str
    sources: list[KnowledgeSourceResponse]

class KnowledgeDocumentResponse(BaseModel):
    id: int
    name: str
    file_path: str
    file_type: str
    category: str | None
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class KnowledgeReingestResponse(BaseModel):
    document_id: int
    chunks: int
    message: str


class KnowledgeStatusResponse(BaseModel):
    documents: int
    chunks: int
    embedded_chunks: int
    categories: dict[str, int]