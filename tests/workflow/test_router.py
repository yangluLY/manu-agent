
import json
from unittest import result  # noqa: F401

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

        # Planner 应生成三个步骤
        assert result["plan"]

        # 工作流应该执行全部步骤
        assert result["current_step"] == len(result["plan"])

        # 执行记录数量正确
        assert len(result["step_results"]) == len(result["plan"])

        # 所有步骤执行成功
        assert all(
            item["status"] == "success"
            for item in result["step_results"]
        )

        # 最后一步为 Summary
        assert result["step_results"][-1]["agent"] == "summary"

        # Response 返回 Summary 的执行结果
        assert result["final_answer"] == (
            result["step_results"][-1]["output"]
        )

        assert result["final_answer"].strip()

    elif route in {"mes", "rag", "bi"}:

        # 普通业务任务统一进入 Simple Planner
        assert len(result["plan"]) == 1

        # Step Executor 执行单步骤
        assert result["current_step"] == 1

        assert len(result["step_results"]) == 1

        step = result["step_results"][0]

        # 验证使用了正确的 Agent
        assert step["agent"] == route

        # 验证执行成功
        assert step["status"] == "success"

        # 验证最终回答来自 Step Executor
        assert result["final_answer"] == step["output"]

        assert result["final_answer"].strip()

        # 验证 V4.5.1 工作流状态
        assert result["workflow_status"] == "completed"

    elif route == "general":

        # General 暂时采用独立节点
        assert result["plan"] == []

        assert len(result["step_results"]) == 1

        step = result["step_results"][0]

        assert step["agent"] == "general"
        assert step["status"] == "success"

        assert result["final_answer"] == step["output"]
        assert result["workflow_status"] == "completed"


def test_invalid_router_output():
    with pytest.raises(ValueError):
        parse_route(
            '{"route": "unknown", "reason": "错误分类"}'
        )


def test_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        parse_route("invalid json")
