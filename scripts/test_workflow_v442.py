
from dotenv import load_dotenv

load_dotenv()

from agent.workflow.factory import get_real_workflow
from services.database.session import SessionLocal


def main():
    # 仅在隔离测试数据库中运行
    with SessionLocal() as db:

        workflow = get_real_workflow(db)

        question = (
            "分析 CNC-001 最近7天的故障情况，"
            "查询相关维修知识，"
            "并给出改善建议"
        )

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

        print("\n=== Router ===")
        print(result["route"])

        print("\n=== Planner ===")
        for step in result["plan"]:
            print(step.id, step.agent, step.task)

        print("\n=== Step Results ===")
        for item in result["step_results"]:
            print(
                item["step_id"],
                item["agent"],
                item["status"],
            )

        print("\n=== Final Answer ===")
        print(result["final_answer"])


if __name__ == "__main__":
    main()
