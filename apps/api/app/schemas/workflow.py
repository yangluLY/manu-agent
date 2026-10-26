
from pydantic import BaseModel, Field

from agent.workflow.schemas.response import WorkflowResponse


class WorkflowChatRequest(BaseModel):
    """
    用户发送给 Workflow Agent 的请求。
    """

    message: str = Field(
        min_length=1,
        max_length=4000,
        description="用户自然语言问题",
    )


class WorkflowChatResponse(WorkflowResponse):
    """
    对外响应。

    复用 V4.5.3 的 WorkflowResponse，
    额外暴露供后续历史查询使用的 thread_id。
    """

    thread_id: str


class WorkflowHealthResponse(BaseModel):
    status: str = "ok"
    service: str = "manuagent-workflow"
