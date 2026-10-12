from typing import Any

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False


class ForeignKeySchema(BaseModel):
    column: str
    referenced_table: str
    referenced_column: str


class TableSchema(BaseModel):
    name: str
    columns: list[ColumnSchema] = Field(default_factory=list)
    foreign_keys: list[ForeignKeySchema] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    tables: list[TableSchema] = Field(default_factory=list)


class SQLGenerationRequest(BaseModel):
    question: str


class SQLGenerationResult(BaseModel):
    sql: str
    explanation: str
    tables: list[str] = Field(default_factory=list)


class SQLValidationResult(BaseModel):
    is_valid: bool

    errors: list[str] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )


class QueryResult(BaseModel):
    columns: list[str] = Field(default_factory=list)

    rows: list[dict[str, Any]] = Field(
        default_factory=list
    )

    row_count: int = 0

    execution_time_ms: float = 0.0

    truncated: bool = False
    

class SQLAttempt(BaseModel):
    attempt: int

    sql: str

    error: str | None = None

    corrected: bool = False


class SQLPipelineResult(BaseModel):
    question: str

    sql: str

    data: QueryResult

    attempts: list[SQLAttempt] = Field(
        default_factory=list
    )

    retry_count: int = 0