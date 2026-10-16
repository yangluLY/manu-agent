
from agent.workflow.state import WorkflowState


def response_node(
    state: WorkflowState,
) -> dict:

    if state["route"] == "complex":

        step_results = state.get(
            "step_results",
            [],
        )

        if not step_results:
            raise ValueError(
                "复合任务没有执行结果"
            )

        if state["current_step"] != len(
            state["plan"]
        ):
            raise ValueError(
                "复合任务尚未执行完成"
            )

        summary_result = step_results[-1]

        if summary_result["agent"] != "summary":
            raise ValueError(
                "复合任务最后一步不是 Summary"
            )

        return {
            "final_answer": summary_result["output"]
        }

    # 普通任务保持原有行为
    return {
        "final_answer": state["result"]
    }
