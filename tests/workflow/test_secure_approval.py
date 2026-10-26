import json
import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from agent.workflow.graph import build_workflow
from agent.workflow.persistence.approval_store import (
    ApprovalConflictError,
    ApprovalStore,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
)
from agent.workflow.persistence.secure_approval import (
    ApprovalPermissionError,
    ApprovalPrincipal,
    SecureApprovalService,
)


@pytest.fixture(scope="module")
def approval_test_dsn():
    """
    初始化审批测试数据库。

    一个测试模块只执行一次。
    """
    load_dotenv()

    dsn = os.getenv("TEST_APPROVAL_DSN")

    if not dsn:
        pytest.skip(
            "未配置 TEST_APPROVAL_DSN"
        )

    store = ApprovalStore(dsn=dsn)

    # 防止误连正式数据库
    with store.connect() as conn:
        database_name = conn.execute(
            "SELECT current_database()"
        ).fetchone()[0]

    if not database_name.endswith("_test"):
        raise RuntimeError(
            f"测试必须使用独立测试数据库，"
            f"当前连接：{database_name}"
        )

    # 初始化审批状态表 + 审批审计表
    store.setup()

    return dsn

def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "审批安全测试",
        })

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


@pytest.fixture
def approval_context(approval_test_dsn):
    """
    为每个测试创建独立的待审批 Workflow。

    使用：
    - LangGraph InMemorySaver
    - PostgreSQL ApprovalStore
    - Mock MES Step Runner
    """

    calls = []

    def runner(step, previous_results):
        calls.append(step.agent)
        return "设备状态正常"

    workflow = build_workflow(
        llm_invoke=mock_llm,
        step_runner=runner,
        checkpointer=InMemorySaver(),
        require_approval=True,
    )

    thread_id = f"test-{uuid4()}"

    result = workflow.invoke(
        initial_state(),
        config=build_thread_config(thread_id),
    )

    assert result.get("__interrupt__")

    workflow_id = (
        result["__interrupt__"][0]
        .value["workflow_id"]
    )

    store = ApprovalStore(
        dsn=approval_test_dsn,
    )

    service = SecureApprovalService(
        workflow=workflow,
        store=store,
    )

    service.register_pending(thread_id)

    return {
        "service": service,
        "store": store,
        "thread_id": thread_id,
        "workflow_id": workflow_id,
        "calls": calls,
    }



def approver():
    return ApprovalPrincipal(
        user_id="test-approver",
        roles=frozenset({"workflow_approver"}),
    )


def test_authorized_approval(approval_context):
    ctx = approval_context

    result = ctx["service"].approve_or_reject(
        thread_id=ctx["thread_id"],
        workflow_id=ctx["workflow_id"],
        approved=True,
        principal=approver(),
    )

    assert result["workflow_status"] == "completed"
    assert ctx["calls"] == ["mes"]


def test_rejected_approval(approval_context):
    ctx = approval_context

    result = ctx["service"].approve_or_reject(
        thread_id=ctx["thread_id"],
        workflow_id=ctx["workflow_id"],
        approved=False,
        principal=approver(),
    )

    assert result["workflow_status"] == "failed"
    assert ctx["calls"] == []


def test_duplicate_approval(approval_context):
    ctx = approval_context

    ctx["service"].approve_or_reject(
        thread_id=ctx["thread_id"],
        workflow_id=ctx["workflow_id"],
        approved=True,
        principal=approver(),
    )

    with pytest.raises(ApprovalConflictError):
        ctx["service"].approve_or_reject(
            thread_id=ctx["thread_id"],
            workflow_id=ctx["workflow_id"],
            approved=True,
            principal=approver(),
        )

    assert ctx["calls"] == ["mes"]


def test_unauthorized_approval(approval_context):
    ctx = approval_context

    unauthorized = ApprovalPrincipal(
        user_id="ordinary-user",
        roles=frozenset({"viewer"}),
    )

    with pytest.raises(ApprovalPermissionError):
        ctx["service"].approve_or_reject(
            thread_id=ctx["thread_id"],
            workflow_id=ctx["workflow_id"],
            approved=True,
            principal=unauthorized,
        )

    assert ctx["calls"] == []


def test_approval_audit(approval_context):
    ctx = approval_context

    ctx["service"].approve_or_reject(
        thread_id=ctx["thread_id"],
        workflow_id=ctx["workflow_id"],
        approved=True,
        principal=approver(),
    )

    with ctx["store"].connect() as conn:
        approval = conn.execute(
            """
            SELECT status, approved, approver_id
            FROM workflow_approvals
            WHERE thread_id = %s
            """,
            (ctx["thread_id"],),
        ).fetchone()

        audit_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM workflow_approval_audit
            WHERE thread_id = %s
            """,
            (ctx["thread_id"],),
        ).fetchone()[0]

    assert approval == (
        "consumed",
        True,
        "test-approver",
    )

    assert audit_count == 1



from concurrent.futures import ThreadPoolExecutor


def test_concurrent_approval_only_once(approval_context):
    ctx = approval_context

    def execute_approval():
        try:
            result = ctx["service"].approve_or_reject(
                thread_id=ctx["thread_id"],
                workflow_id=ctx["workflow_id"],
                approved=True,
                principal=approver(),
            )
            return result["workflow_status"]
        except ApprovalConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(execute_approval)
            for _ in range(2)
        ]

        results = [
            future.result(timeout=30)
            for future in futures
        ]

    assert results.count("completed") == 1
    assert results.count("conflict") == 1

    # 两个审批请求中只有一个进入 Agent
    assert ctx["calls"] == ["mes"]
