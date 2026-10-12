import json

import pytest
from pydantic import ValidationError

from agent.schemas import (
    AgentResponse,
    AgentResponseStatus,
    AgentSource,
    AgentSourceType,
    get_agent_response_format,
)


def build_response() -> AgentResponse:
    return AgentResponse(
        status=AgentResponseStatus.SUCCESS,
        answer="MC-003 当前处于维护状态。",
        highlights=["设备状态为 maintenance"],
        recommendations=["检查该设备尚未完成的维修工单"],
        sources=[
            AgentSource(
                type=AgentSourceType.TOOL,
                name="get_machine_detail",
                description="提供设备基础信息和当前状态。",
                references=["MC-003"],
            )
        ],
        missing_information=[],
    )


def test_agent_response_is_json_serializable():
    response = build_response()

    payload = response.model_dump(mode="json")

    assert payload["status"] == "success"
    assert payload["sources"][0]["name"] == "get_machine_detail"
    json.dumps(payload, ensure_ascii=False)


def test_agent_response_rejects_unknown_fields():
    payload = build_response().model_dump(mode="json")
    payload["unexpected"] = True

    with pytest.raises(ValidationError):
        AgentResponse.model_validate(payload)


def test_response_format_uses_json_schema_without_strict():
    response_format = get_agent_response_format()
    schema = response_format["schema"]

    assert response_format["type"] == "json_schema"
    assert response_format["name"] == "manu_agent_response"
    assert "strict" not in response_format
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "status",
        "answer",
        "highlights",
        "recommendations",
        "sources",
        "missing_information",
    }
