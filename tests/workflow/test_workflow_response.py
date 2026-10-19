
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)


def create_test_state():
    """
    模拟已经完成的 V4.5.2 WorkflowState。
    """

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    source = {
        "document_id": 1,
        "document_name": "设备维修手册",
        "chunk_id": 10,
        "chunk_index": 0,
        "score": 0.95,
        "content": "检查主轴冷却系统",
        "metadata": None,
    }

    return {
        "user_input": "分析 CNC-001 设备故障",
        "workflow_id": str(uuid4()),
        "workflow_status": "completed",
        "route": "complex",
        "route_reason": "需要综合分析",
        "plan": [],
        "current_step": 3,
        "result": "综合建议",
        "final_answer": "建议检查冷却系统并加强维护。",
        "step_results": [
            {
                "step_id": 1,
                "agent": "mes",
                "task": "查询设备故障",
                "status": "success",
                "output": "最近7天发生3次故障",
                "duration_ms": 100.5,
                "data": None,
                "sources": [],
                "sql": None,
                "chart": None,
            },
            {
                "step_id": 2,
                "agent": "rag",
                "task": "查询维修知识",
                "status": "success",
                "output": "检索到维修手册",
                "duration_ms": 200.5,
                "data": None,
                "sources": [source, source],
                "sql": None,
                "chart": None,
            },
            {
                "step_id": 3,
                "agent": "bi",
                "task": "统计故障趋势",
                "status": "success",
                "output": "故障趋势分析完成",
                "duration_ms": 300.5,
                "data": {
                    "analysis": {
                        "summary": "故障集中在主轴"
                    }
                },
                "sources": [],
                "sql": (
                    "SELECT COUNT(*) "
                    "FROM machine_alarms"
                ),
                "chart": {
                    "title": {
                        "text": "故障趋势"
                    },
                    "series": [
                        {
                            "type": "bar",
                            "data": [2, 3, 1],
                        }
                    ],
                },
            },
        ],
        "execution_events": [
            {
                "event_type": "workflow_started",
                "timestamp": timestamp,
            },
            {
                "event_type": "workflow_completed",
                "timestamp": timestamp,
            },
        ],
    }


def test_workflow_response_basic():

    state = create_test_state()

    response = build_workflow_response(
        state
    )

    assert response.workflow_id == (
        state["workflow_id"]
    )

    assert response.status == "completed"

    assert response.route == "complex"

    assert response.answer == (
        state["final_answer"]
    )

    assert len(response.steps) == 3


def test_workflow_response_sources():

    response = build_workflow_response(
        create_test_state()
    )

    # 两条相同来源被聚合为一条
    assert len(response.sources) == 1

    assert response.sources[0].document_name == (
        "设备维修手册"
    )

    assert response.sources[0].chunk_id == 10

    # 原始步骤结果依然保留
    assert len(response.steps[1].sources) == 2


def test_workflow_response_charts():

    response = build_workflow_response(
        create_test_state()
    )

    assert len(response.charts) == 1

    chart = response.charts[0]

    assert chart.agent == "bi"

    assert chart.step_id == 3

    assert chart.option["title"]["text"] == (
        "故障趋势"
    )


def test_workflow_response_sql():

    response = build_workflow_response(
        create_test_state()
    )

    bi_step = response.steps[2]

    assert "machine_alarms" in bi_step.sql

    assert bi_step.data["analysis"]["summary"] == (
        "故障集中在主轴"
    )


def test_workflow_response_events():

    response = build_workflow_response(
        create_test_state()
    )

    assert len(response.execution_events) == 2

    assert response.execution_events[0].event_type == (
        "workflow_started"
    )

    assert response.execution_events[-1].event_type == (
        "workflow_completed"
    )


def test_workflow_response_json():

    response = build_workflow_response(
        create_test_state()
    )

    data = response.model_dump(
        mode="json"
    )

    assert isinstance(data, dict)

    assert data["status"] == "completed"
    assert isinstance(data["steps"], list)
    assert isinstance(data["sources"], list)
    assert isinstance(data["charts"], list)

    # 可以直接序列化为 JSON 字符串
    json_text = response.model_dump_json()

    assert isinstance(json_text, str)


def test_missing_workflow_id():

    state = create_test_state()

    state.pop("workflow_id")

    with pytest.raises(ValueError):
        build_workflow_response(state)


def test_incomplete_workflow():

    state = create_test_state()

    state["workflow_status"] = "running"

    with pytest.raises(ValueError):
        build_workflow_response(state)


def test_missing_final_answer():

    state = create_test_state()

    state["final_answer"] = ""

    with pytest.raises(ValueError):
        build_workflow_response(state)


def test_invalid_step_data():

    state = create_test_state()

    state["step_results"][0]["step_id"] = (
        "invalid"
    )

    with pytest.raises(ValidationError):
        build_workflow_response(state)
