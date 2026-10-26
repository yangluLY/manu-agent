
from dataclasses import dataclass

import psycopg

from agent.workflow.persistence.postgres import (
    get_checkpoint_dsn,
)


@dataclass(frozen=True)
class ApprovalRecord:
    thread_id: str
    workflow_id: str
    status: str


class ApprovalConflictError(Exception):
    """审批记录已被处理或存在冲突。"""


class ApprovalStore:
    """
    PostgreSQL 审批记录存储。

    不负责执行 LangGraph，也不负责身份认证。
    """

    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or get_checkpoint_dsn()

    def connect(self):
        return psycopg.connect(
            self.dsn,
            autocommit=False,
        )
    
    def setup(self) -> None:
        """
        初始化审批记录表和审计表。

        仅负责建表，不删除已有数据。
        可重复执行。
        """
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_approvals (
                    thread_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    approved BOOLEAN,
                    approver_id TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    decided_at TIMESTAMPTZ,

                    CONSTRAINT ck_workflow_approvals_status
                    CHECK (status IN ('pending', 'consumed'))
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_workflow_approvals_status
                ON workflow_approvals (status)
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_approval_audit (
                    id BIGSERIAL PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                    CONSTRAINT ck_workflow_approval_audit_decision
                    CHECK (decision IN ('approved', 'rejected'))
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_workflow_approval_audit_thread
                ON workflow_approval_audit (
                    thread_id,
                    created_at
                )
                """
            )

    def register_pending(
        self,
        *,
        thread_id: str,
        workflow_id: str,
    ) -> ApprovalRecord:
        """
        注册待审批任务。

        要求调用方先确认工作流确实中断在
        approval_gate。

        重复注册同一个 thread_id + workflow_id
        是幂等的，不会重新打开已消费的审批。
        """
        if not thread_id or not workflow_id:
            raise ValueError("审批标识不能为空")

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_approvals (
                    thread_id,
                    workflow_id,
                    status
                )
                VALUES (%s, %s, 'pending')
                ON CONFLICT (thread_id) DO NOTHING
                """,
                (thread_id, workflow_id),
            )

            row = conn.execute(
                """
                SELECT workflow_id, status
                FROM workflow_approvals
                WHERE thread_id = %s
                FOR UPDATE
                """,
                (thread_id,),
            ).fetchone()

            if row is None:
                raise ApprovalConflictError(
                    "无法读取审批记录"
                )

            stored_workflow_id, status = row

            if stored_workflow_id != workflow_id:
                raise ApprovalConflictError(
                    "thread_id 已关联另一个工作流"
                )

            return ApprovalRecord(
                thread_id=thread_id,
                workflow_id=workflow_id,
                status=status,
            )

    def lock_pending(
        self,
        conn,
        *,
        thread_id: str,
        workflow_id: str,
    ) -> None:
        """
        在调用方事务中锁住指定审批。

        行锁保持到事务提交或回滚为止。
        """

        row = conn.execute(
            """
            SELECT workflow_id, status
            FROM workflow_approvals
            WHERE thread_id = %s
            FOR UPDATE
            """,
            (thread_id,),
        ).fetchone()

        if row is None:
            raise ApprovalConflictError(
                "未找到审批记录"
            )

        stored_workflow_id, status = row

        if stored_workflow_id != workflow_id:
            raise ApprovalConflictError(
                "workflow_id 不匹配"
            )

        if status != "pending":
            raise ApprovalConflictError(
                "该审批已经处理，不能重复恢复"
            )

    def record_decision(
        self,
        conn,
        *,
        thread_id: str,
        workflow_id: str,
        actor_id: str,
        approved: bool,
    ) -> None:
        """
        在同一个事务中保存审批结果和审计。

        必须先调用 lock_pending()。
        """

        cursor = conn.execute(
            """
            UPDATE workflow_approvals
            SET
                status = 'consumed',
                approved = %s,
                approver_id = %s,
                decided_at = NOW()
            WHERE thread_id = %s
              AND workflow_id = %s
              AND status = 'pending'
            """,
            (
                approved,
                actor_id,
                thread_id,
                workflow_id,
            ),
        )

        if cursor.rowcount != 1:
            raise ApprovalConflictError(
                "审批状态更新失败"
            )

        conn.execute(
            """
            INSERT INTO workflow_approval_audit (
                thread_id,
                workflow_id,
                actor_id,
                decision
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                thread_id,
                workflow_id,
                actor_id,
                "approved" if approved else "rejected",
            ),
        )
