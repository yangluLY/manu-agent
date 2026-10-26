
"""
V4.8.4.3

PostgreSQL Checkpoint + Secure Approval E2E

测试：
1. 审批通过后恢复
2. 审批拒绝后阻止 Agent 执行
3. 重建 Workflow 后不能重复审批

不调用真实 DeepSeek。
不修改真实 MES 业务数据。
"""

import json
import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver

from agent.workflow.graph import build_workflow
from agent.workflow.persistence.approval_store import (
    ApprovalConflictError,
    ApprovalStore,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
)
from agent.workflow.persistence.secure_approval import (
    ApprovalPrincipal,
    SecureApprovalService,
)


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps(
            {
                "route": "mes",
                "reason": "Checkpoint 恢复测试",
            }
        )

    raise ValueError("未知 Prompt")


def initial_state():
    return {
        "user_input": "查询 CNC-001 状态",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }


def make_runner(calls):
    def runner(step, previous_results):
        calls.append(step.agent)
        return "CNC-001 设备状态正常"

    return runner


def approver():
    return ApprovalPrincipal(
        user_id="test-supervisor",
        roles=frozenset(
            {"workflow_approver"}
        ),
    )


@pytest.fixture(scope="module")
def test_dsn():
    load_dotenv()

    dsn = os.getenv("TEST_APPROVAL_DSN")

    if not dsn:
        pytest.skip(
            "未配置 TEST_APPROVAL_DSN"
        )

    store = ApprovalStore(dsn=dsn)

    with store.connect() as conn:
        database_name = conn.execute(
            "SELECT current_database()"
        ).fetchone()[0]

    if not database_name.endswith("_test"):
        raise RuntimeError(
            "禁止在非测试数据库执行集成测试："
            + database_name
        )

    # 初始化审批表。
    store.setup()

    # 初始化真实 LangGraph Checkpoint 表。
    with PostgresSaver.from_conn_string(dsn) as saver:
        saver.setup()

    return dsn


def start_pending_workflow(dsn, thread_id, calls):
    """
    第一次构建 Workflow，执行到 interrupt()。

    返回 workflow_id。
    """

    with PostgresSaver.from_conn_string(dsn) as saver:

        workflow = build_workflow(
            llm_invoke=mock_llm,
            step_runner=make_runner(calls),
            checkpointer=saver,
            require_approval=True,
        )

        result = workflow.invoke(
            initial_state(),
            config=build_thread_config(thread_id),
        )

        assert result.get("__interrupt__")

        workflow_id = (
            result["__interrupt__"][0]
            .value["workflow_id"]
        )

        # 这里验证 Checkpoint 确实保存到数据库。
        snapshot = workflow.get_state(
            build_thread_config(thread_id)
        )

        assert snapshot is not None
        assert snapshot.next

        store = ApprovalStore(dsn=dsn)

        service = SecureApprovalService(
            workflow=workflow,
            store=store,
        )

        service.register_pending(thread_id)

    # 离开 with：
    # 原 Workflow 的 PostgreSQL 连接已关闭。
    return workflow_id


@pytest.mark.parametrize(
    "approved, expected_status, expected_calls",
    [
        (True, "completed", ["mes"]),
        (False, "failed", []),
    ],
)
def test_resume_after_workflow_recreation(
    test_dsn,
    approved,
    expected_status,
    expected_calls,
):
    """
    两次独立创建 Workflow 和 PostgresSaver。

    验证暂停状态能够从 PostgreSQL 恢复。
    """

    thread_id = f"e2e-{uuid4()}"
    calls = []

    # 第一次执行：生成待审批 Checkpoint。
    workflow_id = start_pending_workflow(
        test_dsn,
        thread_id,
        calls,
    )

    assert calls == []

    # 第二次执行：重新构建 Workflow。
    with PostgresSaver.from_conn_string(
        test_dsn
    ) as saver:

        workflow = build_workflow(
            llm_invoke=mock_llm,
            step_runner=make_runner(calls),
            checkpointer=saver,
            require_approval=True,
        )

        snapshot = workflow.get_state(
            build_thread_config(thread_id)
        )

        # 证明第二个实例读取到了已有状态。
        assert snapshot is not None
        assert snapshot.next

        store = ApprovalStore(dsn=test_dsn)

        service = SecureApprovalService(
            workflow=workflow,
            store=store,
        )

        result = service.approve_or_reject(
            thread_id=thread_id,
            workflow_id=workflow_id,
            approved=approved,
            principal=approver(),
        )

        assert (
            result["workflow_status"]
            == expected_status
        )

        assert calls == expected_calls

        # 审批完成后，不能继续停在审批节点。
        final_snapshot = workflow.get_state(
            build_thread_config(thread_id)
        )

        assert not final_snapshot.next

        with store.connect() as conn:
            approval = conn.execute(
                """
                SELECT
                    status,
                    approved,
                    approver_id
                FROM workflow_approvals
                WHERE thread_id = %s
                """,
                (thread_id,),
            ).fetchone()

            audit = conn.execute(
                """
                SELECT
                    decision,
                    actor_id
                FROM workflow_approval_audit
                WHERE thread_id = %s
                """,
                (thread_id,),
            ).fetchall()

        assert approval == (
            "consumed",
            approved,
            "test-supervisor",
        )

        assert len(audit) == 1

        assert audit[0] == (
            "approved" if approved else "rejected",
            "test-supervisor",
        )


def test_duplicate_approval_after_recreation(
    test_dsn,
):
    """
    工作流恢复完成后再次重新构建实例，
    同一个审批不能被执行第二次。
    """

    thread_id = f"e2e-{uuid4()}"
    calls = []

    workflow_id = start_pending_workflow(
        test_dsn,
        thread_id,
        calls,
    )

    # 第二个 Workflow 实例：第一次审批。
    with PostgresSaver.from_conn_string(
        test_dsn
    ) as saver:

        workflow = build_workflow(
            llm_invoke=mock_llm,
            step_runner=make_runner(calls),
            checkpointer=saver,
            require_approval=True,
        )

        service = SecureApprovalService(
            workflow=workflow,
            store=ApprovalStore(dsn=test_dsn),
        )

        result = service.approve_or_reject(
            thread_id=thread_id,
            workflow_id=workflow_id,
            approved=True,
            principal=approver(),
        )

        assert result["workflow_status"] == "completed"

    assert calls == ["mes"]

    # 第三个 Workflow 实例：重复审批。
    with PostgresSaver.from_conn_string(
        test_dsn
    ) as saver:

        workflow = build_workflow(
            llm_invoke=mock_llm,
            step_runner=make_runner(calls),
            checkpointer=saver,
            require_approval=True,
        )

        store = ApprovalStore(dsn=test_dsn)

        service = SecureApprovalService(
            workflow=workflow,
            store=store,
        )

        with pytest.raises(
            ApprovalConflictError
        ):
            service.approve_or_reject(
                thread_id=thread_id,
                workflow_id=workflow_id,
                approved=True,
                principal=approver(),
            )

        with store.connect() as conn:
            audit_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM workflow_approval_audit
                WHERE thread_id = %s
                """,
                (thread_id,),
            ).fetchone()[0]

        assert audit_count == 1

    # 即使重新创建 Workflow，也不能再执行 MES Agent。
    assert calls == ["mes"]
