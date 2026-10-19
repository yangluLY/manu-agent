
import json
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agent.workflow.graph import build_workflow
from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
)


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "设备状态查询",
        })

    raise ValueError("未知 Prompt")


def initial_state():
    return {
        "user_input": "查询 CNC-001 当前状态",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


def create_test_workflow():
    calls = []

    def mock_runner(step, previous_results):
        calls.append(step.agent)
        return "CNC-001 设备状态正常"

    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
        checkpointer=InMemorySaver(),
        require_approval=True,
    )

    config = build_thread_config(
        str(uuid4())
    )

    return workflow, config, calls


def start_and_get_payload(workflow, config):
    result = workflow.invoke(
        initial_state(),
        config=config,
    )

    assert "__interrupt__" in result
    assert result["__interrupt__"]

    payload = result["__interrupt__"][0].value

    assert payload["type"] == "workflow_approval"

    return payload


def test_workflow_pauses_before_execution():
    workflow, config, calls = create_test_workflow()

    payload = start_and_get_payload(
        workflow,
        config,
    )

    assert payload["step_count"] == 1
    assert payload["agents"] == ["mes"]

    # 审批前绝对没有调用 MES
    assert calls == []

    snapshot = workflow.get_state(config)

    assert "approval_gate" in snapshot.next


def test_approval_resume_success():
    workflow, config, calls = create_test_workflow()

    payload = start_and_get_payload(
        workflow,
        config,
    )

    result = workflow.invoke(
        Command(
            resume={
                "workflow_id": payload["workflow_id"],
                "approved": True,
            }
        ),
        config=config,
    )

    assert calls == ["mes"]

    assert result["approval_status"] == "approved"
    assert result["workflow_status"] == "completed"

    assert result["final_answer"] == (
        "CNC-001 设备状态正常"
    )

    assert len(result["step_results"]) == 1

    response = build_workflow_response(result)

    assert response.status == "completed"
    assert len(response.steps) == 1

    # 工作流已经结束
    snapshot = workflow.get_state(config)
    assert not snapshot.next


def test_approval_rejected():
    workflow, config, calls = create_test_workflow()

    payload = start_and_get_payload(
        workflow,
        config,
    )

    result = workflow.invoke(
        Command(
            resume={
                "workflow_id": payload["workflow_id"],
                "approved": False,
            }
        ),
        config=config,
    )

    # 拒绝以后不应该执行 MES
    assert calls == []

    assert result["approval_status"] == "rejected"
    assert result["workflow_status"] == "failed"

    assert result["step_results"] == []
    assert "未获得人工审批" in result["final_answer"]

    response = build_workflow_response(result)

    assert response.status == "failed"
    assert response.steps == []

    snapshot = workflow.get_state(config)
    assert not snapshot.next


def test_approval_requires_checkpointer():

    with pytest.raises(
        ValueError,
        match="Checkpointer",
    ):
        build_workflow(
            llm_invoke=mock_llm,
            step_runner=lambda step, results: "OK",
            require_approval=True,
        )
