
import json

from agent.workflow.graph import build_workflow
from agent.workflow.schemas.result import AgentOutput

PLAN = {
    "steps": [
        {
            "id": 1,
            "agent": "mes",
            "task": "查询设备故障",
        },
        {
            "id": 2,
            "agent": "bi",
            "task": "分析故障趋势",
        },
        {
            "id": 3,
            "agent": "summary",
            "task": "生成改善建议",
        },
    ]
}


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "complex",
            "reason": "需要多步骤分析",
        })

    if "任务规划器" in system_prompt:
        return json.dumps(PLAN)

    raise ValueError("未知 Prompt")


def mock_runner(step, previous_results):
    return AgentOutput(
        output=f"{step.agent} 执行成功"
    )


def build_initial_state():
    return {
        "user_input": "分析设备故障并给出改善建议",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


def test_workflow_status_completed():
    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
    )

    result = workflow.invoke(
        build_initial_state()
    )

    assert result["workflow_id"]
    assert result["workflow_status"] == "completed"

    assert result["current_step"] == 3
    assert len(result["step_results"]) == 3


def test_workflow_execution_events():
    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
    )

    result = workflow.invoke(
        build_initial_state()
    )

    events = result["execution_events"]

    assert len(events) == 5

    assert events[0]["event_type"] == (
        "workflow_started"
    )

    assert events[-1]["event_type"] == (
        "workflow_completed"
    )

    step_events = [
        event
        for event in events
        if event["event_type"] == "step_completed"
    ]

    assert len(step_events) == 3

    assert [
        event["agent"]
        for event in step_events
    ] == ["mes", "bi", "summary"]

    assert all(
        event["duration_ms"] >= 0
        for event in step_events
    )


def test_workflow_id_unique():
    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
    )

    first = workflow.invoke(
        build_initial_state()
    )

    second = workflow.invoke(
        build_initial_state()
    )

    assert first["workflow_id"] != (
        second["workflow_id"]
    )


def test_step_duration_recorded():
    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
    )

    result = workflow.invoke(
        build_initial_state()
    )

    for item in result["step_results"]:
        assert "duration_ms" in item
        assert item["duration_ms"] >= 0


def test_workflow_final_answer():
    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
    )

    result = workflow.invoke(
        build_initial_state()
    )

    assert result["final_answer"] == (
        result["step_results"][-1]["output"]
    )

    assert result["final_answer"] == (
        "summary 执行成功"
    )
