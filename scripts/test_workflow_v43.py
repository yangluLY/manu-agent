
from dotenv import load_dotenv

from agent.workflow.factory import get_workflow


def main():
    load_dotenv()

    workflow = get_workflow()

    question = (
        "分析 CNC-001 设备最近7天的故障情况，"
        "查询相关维修知识，"
        "并给出改善建议"
    )

    result = workflow.invoke({
        "user_input": question,

        "route": "general",
        "route_reason": "",

        "plan": [],
        "current_step": 0,

        "result": "",
        "final_answer": "",
    })

    print("=" * 60)
    print("用户问题:", question)

    print("\nRouter 结果:")
    print(result["route"])
    print(result["route_reason"])

    print("\nPlanner 结果:")

    for step in result["plan"]:
        print(
            f"Step {step.id} "
            f"[{step.agent}] "
            f"{step.task}"
        )

    print("\nFinal Answer:")
    print(result["final_answer"])


if __name__ == "__main__":
    main()
