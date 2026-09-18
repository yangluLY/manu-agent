from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户发送给 ManuAgent 的消息",
    )


class AgentChatResponse(BaseModel):
    answer: str