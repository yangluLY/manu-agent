from typing import Literal

from pydantic import BaseModel, Field


class AgentHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(
        ...,
        min_length=1,
        max_length=8000,
    )


class AgentChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户发送给 ManuAgent 的消息",
    )
    history: list[AgentHistoryMessage] = Field(
        default_factory=list,
        max_length=50,
        description="当前会话中本条消息之前的对话历史",
    )


class AgentChatResponse(BaseModel):
    answer: str
