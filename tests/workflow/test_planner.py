
import json

import pytest
from pydantic import ValidationError

from agent.workflow.graph import build_workflow
from agent.workflow.nodes.planner import parse_plan

VALID_PLAN = {
    "steps": [
        {
            "id": 1,
            "agent": "mes",
            "task": "查询 CNC-001 设备故障记录",
        },
        {
            "id": 2,
            "agent": "bi",
            "task": "分析故障变化趋势",
        },
        {
            "id": 3,
            "agent": "rag",
            "task": "检索相关维修知识",
        },
        {
            "id": 4,
            "agent": "summary",
            "task": "整理故障分析和改善建议",
        },
    ]
}


def test_parse_valid_plan():
    plan = parse_plan(
        json.dumps(VALID_PLAN)
    )

    assert len(plan.steps) == 4
    assert plan.steps[0].agent == "mes"
    assert plan.steps[-1].agent == "summary"


def test_invalid_agent():
    data = {
        "steps": [
            {
                "id": 1,
                "agent": "unknown",
                "task": "非法任务",
            },
            {
                "id": 2,
                "agent": "summary",
                "task": "总结",
            },
        ]
    }

    with pytest.raises(ValidationError):
        parse_plan(json.dumps(data))


def test_invalid_step_ids():
    data = {
        "steps": [
            {
                "id": 1,
                "agent": "mes",
                "task": "查询设备",
            },
            {
                "id": 3,
                "agent": "summary",
                "task": "总结结果",
            },
        ]
    }

    with pytest.raises(ValidationError):
        parse_plan(json.dumps(data))


def test_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        parse_plan("not json")


def test_workflow_planner():
    """
    验证 complex 任务会进入 Planner。
    不调用真实 DeepSeek。
    """

    def mock_llm(system_prompt, user_input):

        if "任务路由器" in system_prompt:
            return json.dumps({
                "route": "complex",
                "reason": "需要多 Agent 协作",
            })

        if "任务规划器" in system_prompt:
            return json.dumps(VALID_PLAN)

        raise ValueError("未知 Prompt")

    workflow = build_workflow(mock_llm)

    result = workflow.invoke({
        "user_input": "分析设备故障并结合维修知识提出建议",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "result": "",
        "final_answer": "",
    })

    assert result["route"] == "complex"
    assert len(result["plan"]) == 4
    assert result["current_step"] == 0

    assert "Step 1" in result["final_answer"]
    assert "Step 4" in result["final_answer"]
    assert "尚未执行" in result["final_answer"]
