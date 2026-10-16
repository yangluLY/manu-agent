
"""
ManuAgent V4.4.3 真实工作流集成测试。

测试内容：
1. DeepSeek Router 智能路由
2. Planner 生成执行计划
3. MES / RAG / BI 真实执行器
4. Step Executor 多步骤循环
5. RAG 文档引用
6. BI SQL / ECharts 结构化结果
7. Summary 最终回答
8. JSON 序列化检查

运行：
    python -m scripts.test_workflow_v443

注意：
    本脚本会访问真实配置的数据库和模型服务。
    请使用隔离测试数据库，并确保 MES 工具已限制为只读。
"""

import json

from dotenv import load_dotenv

# 加载 .env，必须放在业务模块导入前
load_dotenv()

from agent.workflow.factory import get_real_workflow
from services.database.session import SessionLocal


QUESTION = (
    "分析 CNC-001 设备最近7天的故障情况，"
    "查询相关维修知识，"
    "并结合数据分析提出改善建议。"
)


def build_initial_state(question: str) -> dict:
    """创建 LangGraph 初始状态。"""

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


def print_router_result(result: dict):
    """打印 Router 路由信息。"""

    print("\n" + "=" * 60)
    print("1. Router 路由结果")
    print("=" * 60)

    print("路由类型:", result["route"])
    print("路由原因:", result.get("route_reason", ""))


def print_planner_result(result: dict):
    """打印 Planner 生成的执行计划。"""

    print("\n" + "=" * 60)
    print("2. Planner 执行计划")
    print("=" * 60)

    plan = result.get("plan", [])

    for step in plan:
        print(
            f"Step {step.id} "
            f"[{step.agent.upper()}] "
            f"{step.task}"
        )

    print(f"\n计划步骤数: {len(plan)}")


def inspect_structured_result(result: dict):
    """
    检查 MES/RAG/BI/Summary 结构化执行结果。
    """

    print("\n" + "=" * 60)
    print("3. Step Executor 执行结果")
    print("=" * 60)

    plan = result["plan"]
    steps = result["step_results"]

    # 验证全部执行完成
    assert len(steps) == len(plan), (
        "执行结果数量与计划步骤数量不一致"
    )

    assert result["current_step"] == len(plan), (
        "工作流尚未执行完成"
    )

    for item in steps:

        print("\n" + "-" * 50)

        print("Step ID:", item["step_id"])
        print("Agent:", item["agent"])
        print("Task:", item["task"])
        print("Status:", item["status"])

        output = item.get("output", "")

        print(
            "Output:",
            output[:500] if output else "",
        )

        # 验证每一步执行成功
        assert item["status"] == "success"

        assert isinstance(output, str)
        assert output.strip()

        # RAG 结构化结果
        if item["agent"] == "rag":
            sources = item.get("sources", [])

            print("\nRAG 检索结果")
            print("引用数量:", len(sources))

            for index, source in enumerate(
                sources,
                start=1,
            ):
                print(
                    f"\n来源 {index}: "
                    f"{source['document_name']}"
                )

                print(
                    "Document ID:",
                    source["document_id"],
                )

                print(
                    "Chunk ID:",
                    source["chunk_id"],
                )

                print(
                    "Similarity:",
                    source["score"],
                )

                print(
                    "Content:",
                    source["content"][:200],
                )

        # BI 结构化结果
        elif item["agent"] == "bi":
            print("\nBI 分析结果")

            sql = item.get("sql")
            data = item.get("data")
            chart = item.get("chart")

            print("SQL:", sql)

            if data:
                analysis = data.get(
                    "analysis",
                    {},
                )

                print(
                    "分析总结:",
                    analysis.get("summary"),
                )

                print(
                    "关键发现:",
                    analysis.get("key_findings"),
                )

                print(
                    "改善建议:",
                    analysis.get("recommendations"),
                )

                print(
                    "分析局限:",
                    analysis.get("limitations"),
                )

            print(
                "ECharts 图表存在:",
                chart is not None,
            )

            if chart:
                print(
                    "图表配置:",
                    json.dumps(
                        chart,
                        ensure_ascii=False,
                    )[:500],
                )

    # 最后一步应该是 Summary
    assert steps[-1]["agent"] == "summary"

    # 最终回答来自 Summary
    assert result["final_answer"] == (
        steps[-1]["output"]
    )

    # 检查 JSON 序列化
    json.dumps(
        steps,
        ensure_ascii=False,
    )

    print("\n结构化结果检查通过！")


def print_final_answer(result: dict):
    """打印最终自然语言回答。"""

    print("\n" + "=" * 60)
    print("4. Summary 最终回答")
    print("=" * 60)

    print(result["final_answer"])


def main():
    print("\n启动 ManuAgent V4.4.3 集成测试")

    print("\n用户问题:")
    print(QUESTION)

    # Session 在整个工作流执行期间保持有效
    with SessionLocal() as db:

        workflow = get_real_workflow(db)

        result = workflow.invoke(
            build_initial_state(QUESTION),
            config={
                "recursion_limit": 30,
            },
        )

        # Router 验证
        assert result["route"] == "complex", (
            "当前测试问题应该进入 complex 路由"
        )

        print_router_result(result)

        # Planner 验证
        assert result["plan"], (
            "Planner 未生成执行计划"
        )

        print_planner_result(result)

        # 执行结果验证
        inspect_structured_result(result)

        # 最终回答
        print_final_answer(result)

    print("\n" + "=" * 60)
    print("ManuAgent V4.4.3 集成测试通过")
    print("=" * 60)


if __name__ == "__main__":
    main()
