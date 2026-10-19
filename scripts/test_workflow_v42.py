
from agent.workflow.factory import get_workflow


def main():
    workflow = get_workflow()

    questions = [
        "查询 CNC-001 设备当前状态",
        "CNC 机床出现主轴过热应该如何处理？请查维修手册",
        "统计最近7天的生产产量趋势",
        "你好，介绍一下你自己",
        (
            "分析 CNC-001 最近7天的故障，"
            "结合维修知识提出改善建议"
        ),
    ]

    for question in questions:
        print("\n" + "=" * 60)
        print("用户问题:", question)

        try:
            result = workflow.invoke({
                "user_input": question,
                "route": "general",
                "route_reason": "",
                "result": "",
                "final_answer": "",
            })

            print("路由类型:", result["route"])
            print("路由原因:", result["route_reason"])
            print("最终结果:", result["final_answer"])

        except Exception as exc:
            print("工作流执行失败:", exc)
            raise


if __name__ == "__main__":
    main()
