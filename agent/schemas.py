from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentResponseStatus(str, Enum):
    """Business status of a final ManuAgent answer."""

    SUCCESS = "success"
    NEEDS_INPUT = "needs_input"
    ERROR = "error"


class AgentSourceType(str, Enum):
    """Kinds of factual sources that ManuAgent may cite."""

    TOOL = "tool"
    DATABASE = "database"
    BUSINESS_API = "business_api"
    KNOWLEDGE_BASE = "knowledge_base"


class StructuredOutputModel(BaseModel):
    """Base configuration shared by all Structured Output models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class AgentSource(StructuredOutputModel):
    """A factual source used to produce the final answer."""

    type: AgentSourceType = Field(
        description="来源类型。实时 MES 数据通常使用 tool。",
    )
    name: str = Field(
        description="来源名称，例如 get_machine_alarms。",
    )
    description: str = Field(
        description="该来源为回答提供了什么信息。",
    )
    references: list[str] = Field(
        description="相关业务标识，例如设备编码、工单号或物料编码；没有则为空数组。",
    )


class AgentResponse(StructuredOutputModel):
    """Structured final response returned by ManuAgent."""

    status: AgentResponseStatus = Field(
        description=(
            "回答状态：success 表示已完成；needs_input 表示缺少必要信息；"
            "error 表示工具或业务执行失败。"
        ),
    )
    answer: str = Field(
        description="直接展示给用户的简洁自然语言回答，不包含内部 Tool JSON。",
    )
    highlights: list[str] = Field(
        description="从真实业务数据中提取的关键事实；没有则为空数组。",
    )
    recommendations: list[str] = Field(
        description="基于事实给出的后续建议；没有则为空数组。",
    )
    sources: list[AgentSource] = Field(
        description="本次回答实际使用的事实来源；未使用外部来源时为空数组。",
    )
    missing_information: list[str] = Field(
        description="继续处理所缺少的信息，例如设备编码；信息完整时为空数组。",
    )


AGENT_RESPONSE_SCHEMA_NAME = "manu_agent_response"


def get_agent_response_format() -> dict[str, Any]:
    """Return a DeepSeek/OpenAI Responses API ``text.format`` value.

    The OpenAI Python SDK can alternatively generate this format and parse the
    result automatically with::

        client.responses.parse(..., text_format=AgentResponse)

    ``strict`` is intentionally not added here. The DeepSeek Responses API
    accepts ``type``, ``name`` and ``schema`` for JSON Schema output.
    """

    return {
        "type": "json_schema",
        "name": AGENT_RESPONSE_SCHEMA_NAME,
        "schema": AgentResponse.model_json_schema(),
    }


__all__ = [
    "AGENT_RESPONSE_SCHEMA_NAME",
    "AgentResponse",
    "AgentResponseStatus",
    "AgentSource",
    "AgentSourceType",
    "get_agent_response_format",
]
