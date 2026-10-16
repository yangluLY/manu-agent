
import json
from types import SimpleNamespace

from pydantic import BaseModel

from agent.workflow.executors.bi_executor import (
    create_bi_runner,
)
from agent.workflow.executors.rag_executor import (
    create_rag_runner,
)
from agent.workflow.executors.real import RealStepRunner
from agent.workflow.graph import build_workflow
from agent.workflow.nodes.step_executor import (
    normalize_agent_output,
)
from agent.workflow.schemas.plan import PlanStep
from agent.workflow.schemas.result import AgentOutput


class FakeQueryResult(BaseModel):
    columns: list[str]
    rows: list[dict]


class FakeAnalysis(BaseModel):
    summary: str
    key_findings: list[str]
    recommendations: list[str]
    limitations: list[str]


def test_legacy_string_compatibility():
    result = normalize_agent_output(
        "MES 模拟执行成功"
    )

    assert result.output == "MES 模拟执行成功"
    assert result.sources == []
    assert result.chart is None


def test_rag_sources_preserved():
    fake_source = SimpleNamespace(
        document_id=10,
        document_name="设备维修手册",
        chunk_id=101,
        chunk_index=0,
        score=0.92,
        content="检查主轴冷却系统",
        metadata={"category": "maintenance"},
    )

    fake_retriever = SimpleNamespace(
        search=lambda **kwargs: [fake_source]
    )

    runner = create_rag_runner(fake_retriever)

    step = PlanStep(
        id=1,
        agent="rag",
        task="查询主轴故障维修知识",
    )

    result = runner(step, [])

    assert isinstance(result, AgentOutput)
    assert len(result.sources) == 1
    assert result.sources[0].document_id == 10
    assert result.sources[0].chunk_id == 101
    assert result.sources[0].score == 0.92


def test_bi_chart_preserved():
    echarts_option = {
        "title": {"text": "故障趋势"},
        "xAxis": {
            "type": "category",
            "data": ["周一", "周二"],
        },
        "yAxis": {"type": "value"},
        "series": [{
            "type": "line",
            "data": [2, 3],
        }],
    }

    fake_result = SimpleNamespace(
        question="统计故障趋势",
        sql="SELECT day, count FROM alarm_stats",
        data=FakeQueryResult(
            columns=["day", "count"],
            rows=[{"day": "周一", "count": 2}],
        ),
        analysis=FakeAnalysis(
            summary="故障次数有所上升",
            key_findings=["周二故障次数较高"],
            recommendations=["检查设备运行状态"],
            limitations=[],
        ),
        retry_count=0,
        echarts_option=echarts_option,
    )

    fake_pipeline = SimpleNamespace(
        run=lambda question: fake_result
    )

    runner = create_bi_runner(fake_pipeline)

    step = PlanStep(
        id=1,
        agent="bi",
        task="统计故障趋势",
    )

    result = runner(step, [])

    assert isinstance(result, AgentOutput)
    assert result.sql.startswith("SELECT")
    assert result.chart == echarts_option
    assert result.data["analysis"]["summary"] == (
        "故障次数有所上升"
    )


def test_structured_workflow_integration():
    """
    完整测试：
    Router → Planner → MES → BI → RAG
    → Summary → Response。

    不调用外部 API。
    """

    plan = {
        "steps": [
            {
                "id": 1,
                "agent": "mes",
                "task": "查询故障记录",
            },
            {
                "id": 2,
                "agent": "bi",
                "task": "统计故障趋势",
            },
            {
                "id": 3,
                "agent": "rag",
                "task": "查询维修知识",
            },
            {
                "id": 4,
                "agent": "summary",
                "task": "汇总改善建议",
            },
        ]
    }

    def mock_llm(system_prompt, user_input):
        if "任务路由器" in system_prompt:
            return json.dumps({
                "route": "complex",
                "reason": "需要多 Agent 协作",
            })

        if "任务规划器" in system_prompt:
            return json.dumps(plan)

        raise ValueError("未知 Prompt")

    chart = {
        "title": {"text": "测试图表"},
        "series": [{
            "type": "line",
            "data": [1, 2, 3],
        }],
    }

    def mes_runner(step, previous):
        return AgentOutput(
            output="MES 故障数据查询完成"
        )

    def bi_runner(step, previous):
        assert len(previous) == 1
        return AgentOutput(
            output="BI 故障分析完成",
            sql="SELECT 1",
            data={"count": 3},
            chart=chart,
        )

    def rag_runner(step, previous):
        assert len(previous) == 2
        return AgentOutput(
            output="检索到设备维修知识",
            sources=[{
                "document_id": 1,
                "document_name": "维修手册",
                "chunk_id": 10,
                "chunk_index": 0,
                "score": 0.9,
                "content": "检查主轴冷却系统",
            }],
        )

    def summary_runner(step, previous):
        assert len(previous) == 3
        assert previous[1]["chart"] == chart
        assert previous[2]["sources"][0][
            "document_name"
        ] == "维修手册"

        return AgentOutput(
            output="综合建议：检查主轴冷却系统。"
        )

    real_runner = RealStepRunner(
        mes_runner=mes_runner,
        bi_runner=bi_runner,
        rag_runner=rag_runner,
        summary_runner=summary_runner,
    )

    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=real_runner,
    )

    result = workflow.invoke({
        "user_input": "分析故障并提供维修建议",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    })

    assert result["route"] == "complex"
    assert len(result["step_results"]) == 4
    assert result["current_step"] == 4

    bi_result = result["step_results"][1]
    rag_result = result["step_results"][2]

    assert bi_result["chart"] == chart
    assert bi_result["sql"] == "SELECT 1"

    assert rag_result["sources"][0][
        "document_name"
    ] == "维修手册"

    assert result["final_answer"] == (
        "综合建议：检查主轴冷却系统。"
    )
