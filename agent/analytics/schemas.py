from typing import Any, Literal

from pydantic import BaseModel, Field

from agent.sql.schemas import QueryResult, SQLAttempt


class DataAnalysisResult(BaseModel):
    summary: str

    key_findings: list[str] = Field(
        default_factory=list
    )

    recommendations: list[str] = Field(
        default_factory=list
    )

    limitations: list[str] = Field(
        default_factory=list
    )


ChartType = Literal[
    "bar",
    "line",
    "pie",
    "table",
]


class ChartSeries(BaseModel):
    name: str
    field: str


class ChartSpec(BaseModel):
    type: ChartType

    title: str

    x_field: str | None = None

    y_fields: list[str] = Field(
        default_factory=list
    )

    category_field: str | None = None

    value_field: str | None = None

    series: list[ChartSeries] = Field(
        default_factory=list
    )

    data: list[dict[str, Any]] = Field(
        default_factory=list
    )

    reason: str | None = None


class BIPipelineResult(BaseModel):
    """“自然语言 -> SQL -> 数据 -> 分析 -> 图表”的完整返回结果。"""

    question: str

    sql: str

    data: QueryResult

    analysis: DataAnalysisResult

    chart: ChartSpec

    echarts_option: dict[str, Any] | None = None

    attempts: list[SQLAttempt] = Field(
        default_factory=list
    )

    retry_count: int = 0
