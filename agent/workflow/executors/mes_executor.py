
from agent.agent import ManuAgent
from agent.workflow.schemas.plan import PlanStep
from agent.workflow.schemas.result import AgentOutput


def create_mes_runner(agent: ManuAgent):
    """
    V1 MES Agent 执行器。
    """

    def run(
        step: PlanStep,
        previous_results: list[dict],
    ) -> str:

        if step.agent != "mes":
            raise ValueError("当前步骤不是 MES 任务")

        # V4.4.2 暂时限制为查询任务。
        # 注意：这是入口检查，不是完整权限防护。
        import re


        # V4.4.3 临时保护：
        # 明确的写入或设备控制命令
        WRITE_PATTERNS = [
            r"^(请)?创建",
            r"^(请)?新增",
            r"^(请)?删除",
            r"^(请)?修改",
            r"^(请)?更新",
            r"^(请)?取消",
            r"^(请)?启动",
            r"^(请)?停止",
            r"^(请)?执行停机",
        ]


        def validate_mes_task(task: str) -> None:
            """
            检查明显的写操作命令。

            这是辅助检查，不能代替工具权限控制。
            """

            normalized = task.strip()

            for pattern in WRITE_PATTERNS:
                if re.search(pattern, normalized):
                    raise ValueError(
                        f"MES 工作流禁止执行写操作: {task}"
                    )
                
        print(
            f"[V4 MESExecutor] 正在执行任务: {step.task}"
        )

        validate_mes_task(step.task)

        context = "\n".join(
            f"{item['agent']}: {item['output']}"
            for item in previous_results
        )

        message = (
            "你正在执行 ManuAgent 工作流中的一个 MES 查询步骤。\n"
            "只允许执行只读查询，不得执行新增、修改、删除或设备控制操作。\n"
            "如果无法确认操作是否只读，请拒绝执行。\n\n"
            f"当前任务：{step.task}\n\n"
            f"前序步骤结果：\n{context or '无'}"
        )

        answer = agent.chat(message=message)

        if not answer:
            raise ValueError("MES Agent 返回空结果")

        return AgentOutput(
            output=answer,
        )

    return run
