
import json

from agent.workflow.graph import build_workflow

MOCK_PLAN = {
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
            "agent": "rag",
            "task": "检索维修知识",
        },
        {
            "id": 4,
            "agent": "summary",
            "task": "生成改善建议",
        },
    ]
}


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "complex",
            "reason": "需要多个 Agent 协作",
        })

    if "任务规划器" in system_prompt:
        return json.dumps(MOCK_PLAN)

    raise ValueError("未知 Prompt")


def test_step_executor_loop():
    workflow = build_workflow(mock_llm)

    result = workflow.invoke({
        "user_input": "分析设备故障并给出改善建议",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    })

    assert result["route"] == "complex"

    # 四个步骤都被执行
    assert result["current_step"] == 4
    assert len(result["step_results"]) == 4

    # 顺序正确
    assert [
        item["agent"]
        for item in result["step_results"]
    ] == [
        "mes",
        "bi",
        "rag",
        "summary",
    ]

    # 全部成功
    assert all(
        item["status"] == "success"
        for item in result["step_results"]
    )

    # 最终回答非空
    assert result["final_answer"]


def test_step_result_dependency():
    """
    验证后续步骤能够读取之前的结果。
    """
    received = []

    def tracking_runner(step, previous_results):
        received.append({
            "agent": step.agent,
            "previous_count": len(previous_results),
        })
        return f"{step.agent} completed"

    workflow = build_workflow(
        mock_llm,
        step_runner=tracking_runner,
    )

    result = workflow.invoke({
        "user_input": "执行复合任务",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    })

    assert len(result["step_results"]) == 4

    assert [
        item["previous_count"]
        for item in received
    ] == [0, 1, 2, 3]
