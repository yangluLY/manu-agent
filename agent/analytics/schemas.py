from pydantic import BaseModel, Field


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