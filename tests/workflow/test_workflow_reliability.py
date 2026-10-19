
import json

from agent.sql.errors import SQLValidationError
from agent.workflow.executors.retry_policy import RetryPolicy
from agent.workflow.graph import build_workflow
from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)

PLAN = {
    "steps": [
        {"id": 1, "agent": "mes", "task": "查询设备"},
        {"id": 2, "agent": "bi", "task": "分析故障"},
        {"id": 3, "agent": "summary", "task": "总结"},
    ]
}


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        route = (
            "mes"
            if user_input.startswith("MES:")
            else "complex"
        )
        return json.dumps({
            "route": route,
            "reason": "测试",
        })

    if "任务规划器" in system_prompt:
        return json.dumps(PLAN)

    raise ValueError("未知 Prompt")


def initial_state(question):
    return {
        "user_input": question,
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


def make_workflow(runner, max_retries=2):
    return build_workflow(
        llm_invoke=mock_llm,
        step_runner=runner,
        retry_policy=RetryPolicy(
            max_retries=max_retries,
            base_delay_seconds=0,
        ),
    )


def test_success_without_retry():
    calls = []

    def runner(step, previous):
        calls.append(step.agent)
        return "查询成功"

    workflow = make_workflow(runner)

    result = workflow.invoke(
        initial_state("MES: 查询设备")
    )

    assert result["workflow_status"] == "completed"
    assert result["final_answer"] == "查询成功"
    assert calls == ["mes"]

    step = result["step_results"][0]
    assert step["attempts"] == 1
    assert step["status"] == "success"


def test_timeout_retry_then_success():
    calls = []

    def runner(step, previous):
        calls.append(step.agent)

        if len(calls) < 3:
            raise TimeoutError("临时超时")

        return "第三次执行成功"

    workflow = make_workflow(runner)

    result = workflow.invoke(
        initial_state("MES: 查询设备")
    )

    assert result["workflow_status"] == "completed"
    assert len(calls) == 3

    step = result["step_results"][0]

    assert step["status"] == "success"
    assert step["attempts"] == 3

    retry_events = [
        event
        for event in result["execution_events"]
        if event["event_type"] == "step_retry"
    ]

    assert len(retry_events) == 2


def test_retry_exhausted():
    calls = []

    def runner(step, previous):
        calls.append(step.agent)
        raise TimeoutError("服务超时")

    workflow = make_workflow(runner)

    result = workflow.invoke(
        initial_state("MES: 查询设备")
    )

    assert len(calls) == 3
    assert result["workflow_status"] == "failed"

    step = result["step_results"][0]

    assert step["status"] == "failed"
    assert step["attempts"] == 3
    assert step["error"]["code"] == "TIMEOUT"
    assert step["error"]["retryable"] is True

    response = build_workflow_response(result)

    assert response.status == "failed"
    assert response.steps[0].error.code == "TIMEOUT"


def test_sql_validation_never_retries():
    calls = []

    def runner(step, previous):
        calls.append(step.agent)
        raise SQLValidationError(
            "Unauthorized tables: alarms"
        )

    workflow = make_workflow(runner)

    result = workflow.invoke(
        initial_state("MES: 测试安全校验")
    )

    assert len(calls) == 1
    assert result["workflow_status"] == "failed"

    error = result["step_results"][0]["error"]

    assert error["code"] == "SQL_VALIDATION_ERROR"
    assert error["retryable"] is False
    assert error["attempts"] == 1

    assert "alarms" not in result["final_answer"]


def test_complex_partial_fallback():
    calls = []

    def runner(step, previous):
        calls.append(step.agent)

        if step.agent == "mes":
            return "设备报警查询成功"

        if step.agent == "bi":
            raise ConnectionError("数据库连接中断")

        if step.agent == "summary":
            raise AssertionError(
                "BI 失败后不应该执行 Summary"
            )

    workflow = make_workflow(runner)

    result = workflow.invoke(
        initial_state("综合分析设备故障")
    )

    assert result["route"] == "complex"
    assert result["workflow_status"] == "partial"

    assert calls == ["mes", "bi", "bi", "bi"]

    assert len(result["step_results"]) == 2
    assert result["current_step"] == 2

    assert result["step_results"][0]["status"] == "success"
    assert result["step_results"][1]["status"] == "failed"

    assert "设备报警查询成功" in result["final_answer"]
    assert "未全部完成" in result["final_answer"]

    response = build_workflow_response(result)

    assert response.status == "partial"
    assert len(response.steps) == 2


def test_failure_events():
    def runner(step, previous):
        raise PermissionError("禁止执行")

    workflow = make_workflow(runner)

    result = workflow.invoke(
        initial_state("MES: 测试权限")
    )

    event_types = [
        item["event_type"]
        for item in result["execution_events"]
    ]

    assert "step_failed" in event_types
    assert "workflow_failed" in event_types
    assert "workflow_completed" not in event_types

    assert result["step_results"][0]["error"]["code"] == (
        "PERMISSION_DENIED"
    )
