
import json
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from agent.workflow.graph import build_workflow
from agent.workflow.persistence.history_service import (
    WorkflowHistoryService,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
)


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "测试 Checkpoint History",
        })

    raise ValueError("未知 Prompt")


def mock_runner(step, previous_results):
    return "CNC-001 状态查询成功"


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
def history_context():
    saver = InMemorySaver()

    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
        checkpointer=saver,
    )

    thread_id = str(uuid4())

    result = workflow.invoke(
        initial_state(),
        config=build_thread_config(thread_id),
    )

    service = WorkflowHistoryService(workflow)

    return service, thread_id, result


def test_list_workflow_history(history_context):
    service, thread_id, _ = history_context

    history = service.list_workflow_history(
        thread_id,
        limit=20,
    )

    assert history.thread_id == thread_id
    assert history.total > 1

    assert len(history.checkpoints) == history.total

    assert all(
        checkpoint.checkpoint_id
        for checkpoint in history.checkpoints
    )


def test_latest_state(history_context):
    service, thread_id, result = history_context

    latest = service.get_workflow_state(thread_id)

    assert latest is not None

    assert latest.checkpoint.workflow_status == (
        "completed"
    )

    assert latest.checkpoint.workflow_id == (
        result["workflow_id"]
    )

    assert latest.final_answer == (
        result["final_answer"]
    )

    assert len(latest.executed_steps) == 1


def test_get_checkpoint_by_id(history_context):
    service, thread_id, _ = history_context

    history = service.list_workflow_history(
        thread_id
    )

    checkpoint_id = (
        history.checkpoints[0].checkpoint_id
    )

    detail = service.get_checkpoint_state(
        thread_id,
        checkpoint_id,
    )

    assert detail is not None

    assert detail.checkpoint.checkpoint_id == (
        checkpoint_id
    )



def test_historical_checkpoint(history_context):
    service, thread_id, _ = history_context

    history = service.list_workflow_history(
        thread_id
    )

    assert history.total > 1

    # 最旧的 Checkpoint
    oldest = history.checkpoints[-1]

    detail = service.get_checkpoint_state(
        thread_id,
        oldest.checkpoint_id,
    )

    # 1. Checkpoint 必须存在
    assert detail is not None

    # 2. Checkpoint ID 一致
    assert detail.checkpoint.checkpoint_id == (
        oldest.checkpoint_id
    )

    # 3. Thread ID 一致
    assert detail.checkpoint.thread_id == thread_id

    # 4. 初始 Checkpoint 不应是完成状态
    assert detail.checkpoint.workflow_status != (
        "completed"
    )

    # 5. 初始检查点没有已完成的 Agent 步骤
    assert detail.checkpoint.completed_steps == 0



def test_thread_isolation(history_context):
    service, _, _ = history_context

    unknown_thread = f"unknown-{uuid4()}"

    history = service.list_workflow_history(
        unknown_thread
    )

    assert history.total == 0

    latest = service.get_workflow_state(
        unknown_thread
    )

    assert latest is None


def test_invalid_limit(history_context):
    service, thread_id, _ = history_context

    with pytest.raises(ValueError):
        service.list_workflow_history(
            thread_id,
            limit=0,
        )

    with pytest.raises(ValueError):
        service.list_workflow_history(
            thread_id,
            limit=101,
        )


def test_invalid_checkpoint_id(history_context):
    service, thread_id, _ = history_context

    with pytest.raises(ValueError):
        service.get_checkpoint_state(
            thread_id,
            "",
        )


def test_history_json_serialization(history_context):
    service, thread_id, _ = history_context

    history = service.list_workflow_history(
        thread_id
    )

    data = history.model_dump(
        mode="json"
    )

    assert isinstance(data, dict)

    assert isinstance(
        data["checkpoints"],
        list,
    )

    assert isinstance(
        history.model_dump_json(),
        str,
    )
