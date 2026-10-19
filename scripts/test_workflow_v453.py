
from dotenv import load_dotenv

load_dotenv()

from agent.workflow.factory import get_real_workflow
from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)
from services.database.session import SessionLocal


QUESTION = (
    "分析 CNC-001 设备最近7天的故障情况，"
    "结合维修知识提出改善建议"
)


def build_initial_state(question: str) -> dict:
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


def main():

    print("\n启动 ManuAgent V4.5.3 测试")

    # 真实集成前确保使用隔离测试库，
    # 并确保 MES 工作流工具级只读限制已经生效。
    with SessionLocal() as db:

        workflow = get_real_workflow(db)

        # 1. LangGraph 执行
        result = workflow.invoke(
            build_initial_state(QUESTION),
            config={
                "recursion_limit": 30,
            },
        )

        # 2. WorkflowState -> WorkflowResponse
        response = build_workflow_response(
            result
        )

        # 3. 展示统一结果
        print("\n=== Workflow ===")
        print("ID:", response.workflow_id)
        print("Status:", response.status)
        print("Route:", response.route)

        print("\n=== Steps ===")

        for step in response.steps:
            print(
                step.step_id,
                step.agent,
                step.status,
                step.duration_ms,
            )

            if step.sql:
                print("SQL:", step.sql)

        print("\n=== Sources ===")

        for source in response.sources:
            print(
                source.document_name,
                source.chunk_id,
                source.score,
            )

        print("\n=== Charts ===")

        for chart in response.charts:
            print(
                "Step:",
                chart.step_id,
            )
            print(
                "ECharts:",
                chart.option,
            )

        print("\n=== Final Answer ===")
        print(response.answer)

        # 4. 验证
        assert response.status == "completed"
        assert response.answer
        assert response.steps
        assert response.workflow_id

        # 5. JSON 输出测试
        json_text = response.model_dump_json(
            indent=2
        )

        print("\n=== WorkflowResponse JSON ===")
        print(json_text)

    print("\nV4.5.3 集成测试通过")


if __name__ == "__main__":
    main()
