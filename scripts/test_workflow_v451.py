
from dotenv import load_dotenv

load_dotenv()

from agent.workflow.factory import get_real_workflow
from services.database.session import SessionLocal


def main():
    question = (
        "分析 CNC-001 最近7天的故障情况，"
        "结合维修知识提出改善建议"
    )

    # 使用隔离测试库，确保 MES 工具只读权限已落实
    with SessionLocal() as db:
        workflow = get_real_workflow(db)

        result = workflow.invoke(
            {
                "user_input": question,
                "route": "general",
                "route_reason": "",
                "plan": [],
                "current_step": 0,
                "step_results": [],
                "result": "",
                "final_answer": "",
            },
            config={
                "recursion_limit": 30,
            },
        )

        print("\n=== Workflow ===")
        print("ID:", result["workflow_id"])
        print("Status:", result["workflow_status"])
        print("Route:", result["route"])

        print("\n=== Plan ===")
        for step in result.get("plan", []):
            print(step.id, step.agent, step.task)

        print("\n=== Execution Events ===")
        for event in result["execution_events"]:
            print(
                event["event_type"],
                event.get("agent"),
                event.get("duration_ms"),
            )

        print("\n=== Step Results ===")
        for item in result["step_results"]:
            print(
                item["step_id"],
                item["agent"],
                item["status"],
                item["duration_ms"],
            )

        print("\n=== Final Answer ===")
        print(result["final_answer"])

        assert result["workflow_status"] == "completed"
        assert result["workflow_id"]
        assert result["final_answer"]

        if result["route"] == "complex":
            assert len(result["step_results"]) == len(
                result["plan"]
            )

    print("\nV4.5.1 真实工作流测试通过")


if __name__ == "__main__":
    main()
