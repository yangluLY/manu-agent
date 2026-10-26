
import logging
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import StreamingResponse

from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
)
from agent.workflow.streaming.sse_service import (
    stream_workflow_events,
)
from apps.api.app.dependencies.workflow import (
    get_workflow_runtime,
)
from apps.api.app.schemas.workflow import (
    WorkflowChatRequest,
    WorkflowChatResponse,
    WorkflowHealthResponse,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/workflow",
    tags=["Workflow Agent"],
)


def build_initial_state(message: str) -> dict:
    return {
        "user_input": message,
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


@router.get(
    "/health",
    response_model=WorkflowHealthResponse,
)
def workflow_health():
    return WorkflowHealthResponse()


@router.post(
    "/chat",
    response_model=WorkflowChatResponse,
)
def workflow_chat(
    request: WorkflowChatRequest,
    workflow=Depends(get_workflow_runtime),
):
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="message 不能为空",
        )

    thread_id = str(uuid4())
    config = build_thread_config(thread_id)

    try:
        result = workflow.invoke(
            build_initial_state(message),
            config=config,
        )

        if result.get("__interrupt__"):
            raise HTTPException(
                status_code=409,
                detail="工作流等待人工审批",
            )

        response = build_workflow_response(
            result
        )

        return WorkflowChatResponse(
            thread_id=thread_id,
            **response.model_dump(
                mode="python"
            ),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Workflow execution failed; thread_id=%s",
            thread_id,
        )

        raise HTTPException(
            status_code=500,
            detail="工作流执行异常，请稍后重试。",
        ) from None


@router.post(
    "/chat/stream",
)
def workflow_chat_stream(
    request: WorkflowChatRequest,
    workflow=Depends(get_workflow_runtime),
):
    """
    V4.8.2 SSE 流式工作流。

    POST:
    /api/v1/workflow/chat/stream
    """

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="message 不能为空",
        )

    thread_id = str(uuid4())

    event_generator = stream_workflow_events(
        workflow=workflow,
        message=message,
        thread_id=thread_id,
        initial_state=build_initial_state(
            message
        ),
    )

    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "X-Thread-ID": thread_id,
        },
    )
