
import json

import pytest

from agent.workflow.graph import build_workflow
from agent.workflow.nodes.router import parse_route


VALID_PLAN = {
    "steps": [
        {
            "id": 1,
            "agent": "mes",
            "task": "查询设备故障记录",
        },
        {
            "id": 2,
            "agent": "rag",
            "task": "查询设备维修知识",
        },
        {
            "id": 3,
            "agent": "summary",
            "task": "整理分析结果",
        },
    ]
}


@pytest.mark.parametrize(
    "route",
    ["mes", "rag", "bi", "general", "complex"],
)
def test_workflow_routes(route):
    """
    验证 V4.3 的五种路由。

    不调用真实 DeepSeek。
    """

    def mock_llm(system_prompt, user_input):

        # 模拟 Router
        if "任务路由器" in system_prompt:
            return json.dumps({
                "route": route,
                "reason": "单元测试",
            })

        # 模拟 Planner
        if "任务规划器" in system_prompt:
            return json.dumps(VALID_PLAN)

        raise ValueError("未知 Prompt")

    workflow = build_workflow(mock_llm)

    result = workflow.invoke({
        "user_input": "测试问题",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "result": "",
        "final_answer": "",
    })

    # 1. 验证路由类型
    assert result["route"] == route

    # 2. 验证路由原因
    assert result["route_reason"] == "单元测试"

    # 3. 验证最终回答
    assert result["final_answer"]

    # 4. 验证执行分支
    if route == "complex":
        assert len(result["plan"]) == 3
        assert result["current_step"] == 0
        assert "Step 1" in result["final_answer"]
        assert "Step 3" in result["final_answer"]
        assert "尚未执行" in result["final_answer"]

    else:
        assert "模拟执行" in result["final_answer"]


def test_invalid_router_output():
    with pytest.raises(ValueError):
        parse_route(
            '{"route": "unknown", "reason": "错误分类"}'
        )


def test_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        parse_route("invalid json")
