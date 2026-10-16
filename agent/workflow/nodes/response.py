
from agent.workflow.state import WorkflowState


def response_node(
    state: WorkflowState,
) -> dict:

    # 复合任务：返回计划
    if state["route"] == "complex":

        plan = state.get("plan", [])

        if not plan:
            raise ValueError(
                "复合任务未生成执行计划"
            )

        lines = [
            "ManuAgent 已生成任务执行计划：",
            "",
        ]

        for step in plan:
            lines.append(
                f"Step {step.id} "
                f"[{step.agent.upper()}] "
                f"{step.task}"
            )

        lines.append("")
        lines.append(
            "当前为 V4.3 规划阶段，尚未执行实际业务任务。"
        )

        return {
            "final_answer": "\n".join(lines)
        }

    # 普通任务：沿用 V4.2
    return {
        "final_answer": state["result"]
    }
