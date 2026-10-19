
"""
ManuAgent V4.7.3
PostgreSQL Interrupt & Resume 集成测试。

运行：
python -m scripts.test_workflow_v473
"""

import json
from uuid import uuid4

from langgraph.types import Command

from agent.workflow.graph import build_workflow
from agent.workflow.persistence.postgres import (
    get_postgres_checkpointer,
    build_thread_config,
)
from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "查询设备状态",
        })

    raise ValueError("未知 Prompt")


def mock_runner(step, previous_results):
    print("[MES] Mock Runner 已执行")
    return "CNC-001 设备运行状态正常"


def initial_state():
    return {
        "user_input": "查询 CNC-001 当前设备状态",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


def create_workflow(saver):
    return build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
        checkpointer=saver,
        require_approval=True,
    )


def main():

    thread_id = f"v473-{uuid4()}"

    config = build_thread_config(thread_id)

    print("\n=== V4.7.3 ===")
    print("Thread ID:", thread_id)

    # ---------------------------------------
    # 第一次连接：执行到人工审批处暂停
    # ---------------------------------------
    with get_postgres_checkpointer() as saver:

        workflow = create_workflow(saver)

        result = workflow.invoke(
            initial_state(),
            config=config,
        )

        assert result.get("__interrupt__")

        approval_payload = (
            result["__interrupt__"][0].value
        )

        print("\n工作流暂停，等待审批")
        print(
            json.dumps(
                approval_payload,
                ensure_ascii=False,
                indent=2,
            )
        )

        snapshot = workflow.get_state(config)

        assert "approval_gate" in snapshot.next
        assert snapshot.values["step_results"] == []

        workflow_id = approval_payload["workflow_id"]

    print("\n第一次 PostgreSQL 连接已关闭")

    # ---------------------------------------
    # 第二次连接：恢复同一个 thread_id
    # ---------------------------------------
    with get_postgres_checkpointer() as saver:

        workflow = create_workflow(saver)

        snapshot = workflow.get_state(config)

        assert "approval_gate" in snapshot.next

        print("\n成功读取等待审批的 Checkpoint")

        # 模拟有权限的审批人批准
        result = workflow.invoke(
            Command(
                resume={
                    "workflow_id": workflow_id,
                    "approved": True,
                }
            ),
            config=config,
        )

        print("\n=== 恢复执行结果 ===")

        assert result["approval_status"] == "approved"
        assert result["workflow_status"] == "completed"

        response = build_workflow_response(result)

        print("Status:", response.status)
        print("Answer:", response.answer)

        print(
            response.model_dump_json(
                indent=2
            )
        )

        assert response.status == "completed"
        assert len(response.steps) == 1

        final_snapshot = workflow.get_state(config)

        assert not final_snapshot.next

        print("\n工作流已经完成")

    print("\nV4.7.3 PostgreSQL Resume 测试通过")


if __name__ == "__main__":
    main()
