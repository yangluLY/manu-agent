
import json
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from agent.workflow.graph import build_workflow
from agent.workflow.persistence.postgres import (
    build_thread_config,
)
from agent.workflow.persistence.resume_service import (
    WorkflowResumeError,
    WorkflowResumeService,
)


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "恢复安全测试",
        })

    raise ValueError("未知 Prompt")


def initial_state():
    return {
        "user_input": "查询 CNC-001 状态",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


@pytest.fixture
def context():
    calls = []

    def runner(step, previous_results):
        calls.append(step.agent)
        return "设备状态正常"

    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=runner,
        checkpointer=InMemorySaver(),
        require_approval=True,
    )

    thread_id = str(uuid4())
    config = build_thread_config(thread_id)

    first_result = workflow.invoke(
        initial_state(),
        config=config,
    )

    assert first_result.get("__interrupt__")

    workflow_id = (
        first_result["__interrupt__"][0]
        .value["workflow_id"]
    )

    service = WorkflowResumeService(workflow)

    return {
        "service": service,
        "thread_id": thread_id,
        "workflow_id": workflow_id,
        "calls": calls,
    }


def test_pending_approval(context):
    service = context["service"]

    pending = service.get_pending_approval(
        context["thread_id"]
    )

    assert pending["workflow_id"] == (
        context["workflow_id"]
    )

    assert pending["next_nodes"] == [
        "approval_gate"
    ]

    assert pending["interrupt_count"] >= 1

    # 审批前没有执行业务 Agent
    assert context["calls"] == []


def test_resume_approved(context):
    result = context["service"].resume(
        thread_id=context["thread_id"],
        workflow_id=context["workflow_id"],
        approved=True,
    )

    assert result["workflow_status"] == "completed"
    assert result["approval_status"] == "approved"

    assert context["calls"] == ["mes"]
    assert len(result["step_results"]) == 1


def test_resume_rejected(context):
    result = context["service"].resume(
        thread_id=context["thread_id"],
        workflow_id=context["workflow_id"],
        approved=False,
    )

    assert result["workflow_status"] == "failed"
    assert result["approval_status"] == "rejected"

    assert context["calls"] == []
    assert result["step_results"] == []


def test_duplicate_resume_rejected(context):
    service = context["service"]

    service.resume(
        thread_id=context["thread_id"],
        workflow_id=context["workflow_id"],
        approved=True,
    )

    with pytest.raises(WorkflowResumeError):
        service.resume(
            thread_id=context["thread_id"],
            workflow_id=context["workflow_id"],
            approved=True,
        )

    assert context["calls"] == ["mes"]


def test_invalid_workflow_id(context):
    with pytest.raises(
        WorkflowResumeError,
        match="workflow_id",
    ):
        context["service"].resume(
            thread_id=context["thread_id"],
            workflow_id="wrong-workflow-id",
            approved=True,
        )

    assert context["calls"] == []


def test_invalid_approval_type(context):
    with pytest.raises(
        WorkflowResumeError,
        match="approved",
    ):
        context["service"].resume(
            thread_id=context["thread_id"],
            workflow_id=context["workflow_id"],
            approved="false",
        )

    assert context["calls"] == []


def test_unknown_thread(context):
    with pytest.raises(WorkflowResumeError):
        context["service"].get_pending_approval(
            str(uuid4())
        )
