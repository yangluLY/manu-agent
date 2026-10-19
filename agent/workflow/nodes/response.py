
from agent.workflow.schemas.execution import ExecutionEvent
from agent.workflow.state import WorkflowState


def response_node(state: WorkflowState) -> dict:
    """
    根据 Step Results 生成最终响应。

    - 全部成功 -> completed
    - 部分成功 -> partial
    - 全部失败 -> failed
    """

    step_results = state.get(
        "step_results",
        [],
    )

    if not step_results:
        raise ValueError(
            "工作流没有执行记录"
        )

    successful_steps = [
        item
        for item in step_results
        if item["status"] == "success"
    ]

    failed_steps = [
        item
        for item in step_results
        if item["status"] == "failed"
    ]

    plan = state.get("plan", [])

    if not failed_steps:
        # 成功情况：检查所有步骤已完成
        if plan:
            if (
                state["current_step"] != len(plan)
                or len(step_results) != len(plan)
            ):
                raise ValueError(
                    "工作流计划尚未执行完成"
                )

            for planned, executed in zip(
                plan,
                step_results,
            ):
                if (
                    planned.id != executed["step_id"]
                    or planned.agent != executed["agent"]
                ):
                    raise ValueError(
                        "计划步骤与执行记录不一致"
                    )

        if not successful_steps:
            raise ValueError(
                "工作流没有成功执行的步骤"
            )

        status = "completed"
        answer = successful_steps[-1]["output"]
        event_type = "workflow_completed"

    elif successful_steps:
        # 部分成功：保留已有结果，不伪造总结
        status = "partial"
        event_type = "workflow_partial"

        completed_text = "\n".join(
            (
                f"步骤 {item['step_id']} "
                f"({item['agent']}): "
                f"{item['output']}"
            )
            for item in successful_steps
        )

        failed_text = "\n".join(
            (
                f"步骤 {item['step_id']} "
                f"({item['agent']}): "
                f"{item['output']}"
            )
            for item in failed_steps
        )

        answer = (
            "本次分析未全部完成，"
            "以下仅为已成功执行的步骤结果，"
            "不能视为完整分析结论。\n\n"
            f"已完成：\n{completed_text}\n\n"
            f"未完成：\n{failed_text}"
        )

    else:
        # 没有成功的步骤
        status = "failed"
        event_type = "workflow_failed"

        failed_text = "\n".join(
            item["output"]
            for item in failed_steps
        )

        answer = (
            "本次工作流执行失败，"
            "未获得可用的业务分析结果。\n"
            f"{failed_text}"
        )

    if not answer.strip():
        raise ValueError(
            "最终回答不能为空"
        )

    event = ExecutionEvent(
        event_type=event_type,
        details={
            "route": state["route"],
            "successful_steps": len(successful_steps),
            "failed_steps": len(failed_steps),
            "planned_steps": len(plan),
        },
    )

    return {
        "final_answer": answer,
        "workflow_status": status,
        "execution_events": [
            *state.get("execution_events", []),
            event.model_dump(mode="json"),
        ],
    }
