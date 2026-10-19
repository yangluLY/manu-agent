
"""
ManuAgent V4.7.2
PostgreSQL Checkpoint History 集成测试。

运行：
python -m scripts.test_workflow_v472
"""

import json
from uuid import uuid4

from agent.workflow.graph import build_workflow
from agent.workflow.persistence.history_service import (
    WorkflowHistoryService,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
    get_postgres_checkpointer,
)


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "Checkpoint History 集成测试",
        })

    raise ValueError("未知 Prompt")


def mock_runner(step, previous_results):
    return "CNC-001 设备状态正常"


def initial_state():
    return {
        "user_input": "查询 CNC-001 设备状态",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


def create_workflow(checkpointer):
    return build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
        checkpointer=checkpointer,
    )


def main():
    thread_id = f"v472-{uuid4()}"

    print("\n=== V4.7.2 PostgreSQL History ===")
    print("Thread ID:", thread_id)

    # 第一阶段：执行工作流并保存检查点
    with get_postgres_checkpointer() as saver:
        workflow = create_workflow(saver)

        result = workflow.invoke(
            initial_state(),
            config=build_thread_config(thread_id),
        )

        assert result["workflow_status"] == "completed"

        expected_workflow_id = result["workflow_id"]
        expected_answer = result["final_answer"]

    print("\n第一次数据库连接已关闭")

    # 第二阶段：重新连接 PostgreSQL 读取历史
    with get_postgres_checkpointer() as saver:
        workflow = create_workflow(saver)
        service = WorkflowHistoryService(workflow)

        history = service.list_workflow_history(
            thread_id,
            limit=30,
        )

        print("\n=== Checkpoint History ===")
        print("历史检查点数量:", history.total)

        assert history.total > 1

        for checkpoint in history.checkpoints:
            print(
                "Checkpoint:",
                checkpoint.checkpoint_id,
                "| Step:",
                checkpoint.step,
                "| Status:",
                checkpoint.workflow_status,
                "| Next:",
                checkpoint.next_nodes,
            )

        # 读取最新状态
        latest = service.get_workflow_state(
            thread_id
        )

        assert latest is not None

        print("\n=== Latest State ===")
        print(
            latest.model_dump_json(
                indent=2
            )
        )

        assert latest.checkpoint.workflow_id == (
            expected_workflow_id
        )

        assert latest.final_answer == expected_answer

        assert latest.checkpoint.workflow_status == (
            "completed"
        )

        # 按 checkpoint_id 读取
        checkpoint_id = (
            history.checkpoints[-1].checkpoint_id
        )

        historical = service.get_checkpoint_state(
            thread_id,
            checkpoint_id,
        )

        assert historical is not None

        assert historical.checkpoint.checkpoint_id == (
            checkpoint_id
        )

        print("\n=== Historical Checkpoint ===")
        print(
            historical.model_dump_json(
                indent=2
            )
        )

    print("\nV4.7.2 PostgreSQL History 测试通过")


if __name__ == "__main__":
    main()
