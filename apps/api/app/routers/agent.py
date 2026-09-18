import logging

from fastapi import APIRouter, Depends, HTTPException
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
            request.message
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