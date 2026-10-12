import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from agent.factory import create_manu_agent
from apps.api.app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
)
from services.database.session import get_db

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post(
    "/chat",
    response_model=AgentChatResponse,
)
def chat(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
):
    try:
        agent = create_manu_agent(db)

        answer = agent.chat(
            request.message,
            history=[
                item.model_dump()
                for item in request.history
            ],
        )

        return AgentChatResponse(
            answer=answer
        )

    except Exception:
        logger.exception(
            "ManuAgent chat failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Agent request failed",
        )


@router.post("/chat/stream")
def chat_stream(
    request: AgentChatRequest,
    db: Session = Depends(get_db, scope="request"),
):
    """以 NDJSON 增量返回 ManuAgent 的状态和回答文本。"""
    try:
        agent = create_manu_agent(db)
    except Exception as error:
        logger.exception("ManuAgent initialization failed")
        raise HTTPException(
            status_code=500,
            detail="Agent initialization failed",
        ) from error

    history = [
        item.model_dump()
        for item in request.history
    ]

    def generate_events():
        try:
            for event in agent.chat_stream(
                request.message,
                history=history,
            ):
                yield json.dumps(
                    event,
                    ensure_ascii=False,
                ) + "\n"
        except GeneratorExit:
            raise
        except Exception:
            logger.exception("ManuAgent streaming chat failed")
            yield json.dumps(
                {
                    "type": "error",
                    "message": "Agent request failed",
                },
                ensure_ascii=False,
            ) + "\n"

    return StreamingResponse(
        generate_events(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
