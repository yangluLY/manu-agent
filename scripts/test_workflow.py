from agent.workflow.graph import build_workflow


def main():
    workflow = build_workflow()

    questions = [
        "查询 CNC-001 设备状态",
        "查询设备维修知识",
        "统计最近7天生产数据",
        "你好",
    ]

    for question in questions:
        result = workflow.invoke({
            "user_input": question,
            "route": "",
            "result": "",
            "final_answer": "",
        })

        print("=" * 50)
        print("用户问题:", question)
        print("路由结果:", result["route"])
        print("最终回答:", result["final_answer"])


if __name__ == "__main__":
    main()