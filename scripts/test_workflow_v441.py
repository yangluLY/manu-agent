from dotenv import load_dotenv

from agent.workflow.factory import get_workflow


def main():
    load_dotenv()

    workflow = get_workflow()

    question = (
        "分析 CNC-001 最近7天的故障情况，"
        "结合维修知识提出改善建议"
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
        print(item["output"])

    print("\n=== Final Answer ===")
    print(result["final_answer"])

    assert result["route"] == "complex"
    assert len(result["plan"]) == len(
        result["step_results"]
    )
    assert result["current_step"] == len(
        result["plan"]
    )


if __name__ == "__main__":
    main()