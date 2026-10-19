
import json
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver

from agent.workflow.graph import build_workflow
from agent.workflow.persistence.postgres import (
    build_thread_config,
)


def mock_llm(system_prompt, user_input):

    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "测试单步骤设备查询",
        })

    raise ValueError("未知 Prompt")


def mock_runner(step, previous_results):
    return "CNC-001 当前运行状态正常"


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


def test_checkpoint_persists_state():

    saver = InMemorySaver()

    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
        checkpointer=saver,
    )

    thread_id = str(uuid4())
    config = build_thread_config(thread_id)

    result = workflow.invoke(
        initial_state(),
        config=config,
    )

    snapshot = workflow.get_state(config)

    assert result["workflow_status"] == "completed"

    assert snapshot.values["workflow_status"] == (
        "completed"
    )

    assert snapshot.values["final_answer"] == (
        result["final_answer"]
    )

    assert snapshot.values["workflow_id"] == (
        result["workflow_id"]
    )


def test_checkpoint_thread_isolation():

    saver = InMemorySaver()

    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
        checkpointer=saver,
    )

    first_config = build_thread_config(
        str(uuid4())
    )

    second_config = build_thread_config(
        str(uuid4())
    )

    first = workflow.invoke(
        initial_state(),
        config=first_config,
    )

    second = workflow.invoke(
        initial_state(),
        config=second_config,
    )

    assert first["workflow_id"] != (
        second["workflow_id"]
    )

    first_snapshot = workflow.get_state(
        first_config
    )

    second_snapshot = workflow.get_state(
        second_config
    )

    assert first_snapshot.values["workflow_id"] == (
        first["workflow_id"]
    )

    assert second_snapshot.values["workflow_id"] == (
        second["workflow_id"]
    )


def test_checkpoint_history_exists():

    saver = InMemorySaver()

    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
        checkpointer=saver,
    )

    config = build_thread_config(
        str(uuid4())
    )

    workflow.invoke(
        initial_state(),
        config=config,
    )

    history = list(
        workflow.get_state_history(config)
    )

    assert len(history) > 1

    assert history[0].values[
        "workflow_status"
    ] == "completed"
