from agent.workflow.schemas.plan import PlanStep


def mock_step_runner(
    step: PlanStep,
    previous_results: list[dict],
) -> str:
    """
    模拟执行 Planner 生成的一个步骤。

    step: 当前步骤
    previous_results: 已完成步骤的结果
    """

    previous_count = len(previous_results)

    if step.agent == "mes":
        return (
            "[模拟MES结果] "
            "CNC-001 最近7天发生3次故障。"
            f"此前已完成{previous_count}步。"
        )

    if step.agent == "bi":
        return (
            "[模拟BI结果] "
            "故障主要与主轴过热有关，"
            "建议进一步分析停机时间。"
            f"此前已完成{previous_count}步。"
        )

    if step.agent == "rag":
        return (
            "[模拟RAG结果] "
            "相关维修知识建议检查冷却系统、"
            "润滑系统和主轴运行参数。"
            f"此前已完成{previous_count}步。"
        )

    if step.agent == "summary":
        content = "\n".join(
            str(item["output"])
            for item in previous_results
        )

        return (
            "[模拟Summary结果]\n"
            "根据前面执行的任务：\n"
            f"{content}\n"
            "建议制定设备预防性维护计划。"
        )

    raise ValueError(
        f"不支持的执行器类型: {step.agent}"
    )