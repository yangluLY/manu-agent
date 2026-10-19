
"""
ManuAgent V4.7.1
PostgreSQL Checkpoint 集成测试。

运行：
python -m scripts.test_workflow_v471
"""

import json
from uuid import uuid4

from agent.workflow.graph import build_workflow
from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
    get_postgres_checkpointer,
)


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "测试 Checkpoint 持久化",
        })

    raise ValueError(
        "本测试不应进入 LLM Planner"
    )


def mock_runner(step, previous_results):
    return (
        "模拟 MES 查询成功："
        "CNC-001 当前运行正常"
    )


def initial_state():
    return {
        "user_input": "查询 CNC-001 当前状态",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


def main():

    thread_id = f"v471-{uuid4()}"

    config = build_thread_config(
        thread_id
    )

    print("\n========== V4.7.1 ==========")
    print("Thread ID:", thread_id)

    # ====================================
    # 第一次连接：执行并保存
    # ====================================

    with get_postgres_checkpointer() as saver:

        workflow = build_workflow(
            llm_invoke=mock_llm,
            step_runner=mock_runner,
            checkpointer=saver,
        )

        result = workflow.invoke(
            initial_state(),
            config=config,
        )

        response = build_workflow_response(
            result
        )

        print("\n第一次执行成功")
        print("Workflow ID:", response.workflow_id)
        print("Status:", response.status)
        print("Answer:", response.answer)

        assert response.status == "completed"
        assert len(response.steps) == 1

        saved_workflow_id = response.workflow_id
        saved_answer = response.answer

    # ====================================
    # 第二次连接：重新读取数据库
    # ====================================

    print("\n第一次数据库连接已关闭")

    with get_postgres_checkpointer() as saver:

        # 新建 LangGraph 实例，
        # 不是沿用之前的 workflow。
        workflow = build_workflow(
            llm_invoke=mock_llm,
            step_runner=mock_runner,
            checkpointer=saver,
        )

        snapshot = workflow.get_state(
            config
        )

        assert snapshot.values, (
            "没有找到持久化 Checkpoint"
        )

        recovered_state = snapshot.values

        print("\n第二次连接读取成功")

        print(
            "Workflow ID:",
            recovered_state["workflow_id"],
        )

        print(
            "Status:",
            recovered_state["workflow_status"],
        )

        print(
            "Answer:",
            recovered_state["final_answer"],
        )

        assert (
            recovered_state["workflow_id"]
            == saved_workflow_id
        )

        assert (
            recovered_state["final_answer"]
            == saved_answer
        )

        assert (
            recovered_state["workflow_status"]
            == "completed"
        )

        history = list(
            workflow.get_state_history(config)
        )

        print(
            "\nCheckpoint 历史数量:",
            len(history),
        )

        assert len(history) > 1

        assert not snapshot.next, (
            "当前测试工作流应已结束，"
            "不应该还有待执行节点"
        )

        # 再次转换成 WorkflowResponse
        response = build_workflow_response(
            recovered_state
        )

        print("\n恢复后的 WorkflowResponse")
        print(
            response.model_dump_json(
                indent=2
            )
        )

    print("\nV4.7.1 PostgreSQL 持久化测试通过")


if __name__ == "__main__":
    main()
