
"""
ManuAgent V4.8.3

Workflow Thread Ownership Store

负责：
1. 工作流归属登记
2. 用户访问权限检查
3. 禁止跨用户访问工作流
"""

import psycopg

from agent.workflow.persistence.postgres import (
    get_checkpoint_dsn,
)


class WorkflowAccessDenied(Exception):
    """工作流不存在或当前用户无权访问。"""


class WorkflowThreadConflict(Exception):
    """thread_id 已归属于其他用户。"""


class WorkflowThreadStore:
    def __init__(
        self,
        dsn: str | None = None,
    ):
        self.dsn = dsn or get_checkpoint_dsn()

    @staticmethod
    def _validate_id(
        value: str,
        name: str,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(  # noqa: TRY004
                f"{name} 必须是字符串"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{name} 不能为空"
            )

        return value

    def register(
        self,
        thread_id: str,
        owner_id: str,
    ) -> None:
        """
        登记工作流所属用户。

        同一用户重复登记同一 thread_id：允许。
        不同用户登记相同 thread_id：拒绝。
        """

        thread_id = self._validate_id(
            thread_id,
            "thread_id",
        )

        owner_id = self._validate_id(
            owner_id,
            "owner_id",
        )

        with psycopg.connect(self.dsn) as conn:
            conn.execute(
                """
                INSERT INTO workflow_threads (
                    thread_id,
                    owner_id
                )
                VALUES (%s, %s)
                ON CONFLICT (thread_id) DO NOTHING
                """,
                (thread_id, owner_id),
            )

            row = conn.execute(
                """
                SELECT owner_id
                FROM workflow_threads
                WHERE thread_id = %s
                """,
                (thread_id,),
            ).fetchone()

            if row is None:
                raise WorkflowThreadConflict(
                    "工作流登记失败"
                )

            if row[0] != owner_id:
                raise WorkflowThreadConflict(
                    "thread_id 已归属于其他用户"
                )

    def assert_owner(
        self,
        thread_id: str,
        user_id: str,
    ) -> None:
        """
        验证工作流归属。

        统一使用相同异常，
        防止向调用方泄露其他用户的工作流是否存在。
        """

        thread_id = self._validate_id(
            thread_id,
            "thread_id",
        )

        user_id = self._validate_id(
            user_id,
            "user_id",
        )

        with psycopg.connect(self.dsn) as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM workflow_threads
                WHERE thread_id = %s
                  AND owner_id = %s
                """,
                (thread_id, user_id),
            ).fetchone()

        if row is None:
            raise WorkflowAccessDenied(
                "工作流不存在或无访问权限"
            )

    def get_owner(
        self,
        thread_id: str,
    ) -> str | None:
        """
        内部管理方法。

        只能在可信服务内部调用，
        不直接暴露成公开 HTTP 接口。
        """

        thread_id = self._validate_id(
            thread_id,
            "thread_id",
        )

        with psycopg.connect(self.dsn) as conn:
            row = conn.execute(
                """
                SELECT owner_id
                FROM workflow_threads
                WHERE thread_id = %s
                """,
                (thread_id,),
            ).fetchone()

        return row[0] if row else None
