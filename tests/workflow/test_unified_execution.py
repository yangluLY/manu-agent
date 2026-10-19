
import json

import pytest

from agent.workflow.graph import build_workflow
from agent.workflow.schemas.result import AgentOutput

COMPLEX_PLAN = {
    "steps": [
        {
            "id": 1,
            "agent": "mes",
            "task": "查询设备故障记录",
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
            "task": "生成综合分析报告",
        },
    ]
}


def mock_llm(system_prompt, user_input):
    """
    模拟 Router 和 Planner。
    根据输入显式选择路由。
    """

    if "任务路由器" in system_prompt:

        if user_input.startswith("MES:"):
            route = "mes"

        elif user_input.startswith("RAG:"):
            route = "rag"

        elif user_input.startswith("BI:"):
            route = "bi"

        elif user_input.startswith("GENERAL:"):
            route = "general"

        else:
            route = "complex"

        return json.dumps({
            "route": route,
            "reason": "V4.5.2 单元测试",
        })

    if "任务规划器" in system_prompt:
        return json.dumps(COMPLEX_PLAN)

    raise ValueError("未知 Prompt")


def mock_runner(step, previous_results):
    """
    模拟结构化 Agent 执行器。
    """

    if step.agent == "mes":
        return AgentOutput(
            output="MES 查询完成",
            data={
                "machine_code": "CNC-001",
                "status": "running",
            },
        )

    if step.agent == "rag":
        return AgentOutput(
            output="RAG 知识检索完成",
            sources=[
                {
                    "document_id": 1,
                    "document_name": "设备维修手册",
                    "chunk_id": 10,
                    "chunk_index": 0,
                    "score": 0.95,
                    "content": "检查主轴冷却系统",
                }
            ],
        )

    if step.agent == "bi":
        return AgentOutput(
            output="BI 数据分析完成",
            sql="SELECT COUNT(*) FROM machine_alarms",
            data={
                "analysis": {
                    "summary": "故障统计完成"
                }
            },
            chart={
                "title": {
                    "text": "设备故障趋势"
                },
                "series": [
                    {
                        "type": "bar",
                        "data": [1, 3, 2],
                    }
                ],
            },
        )

    if step.agent == "summary":
        return AgentOutput(
            output="综合建议：加强设备预防性维护。",
        )

    raise ValueError(
        f"未知 Agent: {step.agent}"
    )


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


@pytest.fixture
def workflow():
    return build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
    )


@pytest.mark.parametrize(
    "route",
    ["mes", "rag", "bi"],
)
def test_simple_task_execution(workflow, route):

    result = workflow.invoke(
        initial_state(f"{route.upper()}: 测试任务")
    )

    assert result["route"] == route
    assert len(result["plan"]) == 1
    assert result["plan"][0].agent == route

    assert result["current_step"] == 1
    assert len(result["step_results"]) == 1

    step = result["step_results"][0]

    assert step["agent"] == route
    assert step["status"] == "success"

    assert result["final_answer"] == step["output"]
    assert result["workflow_status"] == "completed"


def test_rag_structured_sources(workflow):

    result = workflow.invoke(
        initial_state("RAG: 查询维修手册")
    )

    step = result["step_results"][0]

    assert len(step["sources"]) == 1

    assert step["sources"][0][
        "document_name"
    ] == "设备维修手册"

    assert step["sources"][0]["chunk_id"] == 10


def test_bi_structured_chart(workflow):

    result = workflow.invoke(
        initial_state("BI: 统计设备故障")
    )

    step = result["step_results"][0]

    assert step["sql"] == (
        "SELECT COUNT(*) FROM machine_alarms"
    )

    assert step["chart"]["title"]["text"] == (
        "设备故障趋势"
    )


def test_complex_workflow(workflow):

    result = workflow.invoke(
        initial_state(
            "分析设备故障并结合维修知识提出建议"
        )
    )

    assert result["route"] == "complex"

    assert len(result["plan"]) == 4
    assert len(result["step_results"]) == 4

    assert result["current_step"] == 4

    assert [
        item["agent"]
        for item in result["step_results"]
    ] == [
        "mes",
        "bi",
        "rag",
        "summary",
    ]

    assert result["final_answer"] == (
        "综合建议：加强设备预防性维护。"
    )


def test_general_structured_result(workflow):

    result = workflow.invoke(
        initial_state("GENERAL: 你好")
    )

    assert result["route"] == "general"
    assert result["workflow_status"] == "completed"

    assert result["plan"] == []
    assert len(result["step_results"]) == 1

    step = result["step_results"][0]

    assert step["agent"] == "general"
    assert step["status"] == "success"

    assert result["final_answer"] == (
        step["output"]
    )


@pytest.mark.parametrize(
    "question,expected_steps",
    [
        ("MES: 查询设备", 1),
        ("RAG: 检索知识", 1),
        ("BI: 查询趋势", 1),
        ("GENERAL: 你好", 1),
        ("分析设备故障并提出建议", 4),
    ],
)
def test_unified_execution_events(
    workflow,
    question,
    expected_steps,
):

    result = workflow.invoke(
        initial_state(question)
    )

    events = result["execution_events"]

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

    assert len(step_events) == expected_steps

    assert len(result["step_results"]) == (
        expected_steps
    )

    assert all(
        event["duration_ms"] >= 0
        for event in step_events
    )
