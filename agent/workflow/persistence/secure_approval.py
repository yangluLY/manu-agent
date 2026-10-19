
from dataclasses import dataclass
from typing import Any

from agent.workflow.persistence.approval_store import (
    ApprovalStore,
)
from agent.workflow.persistence.resume_service import (
    WorkflowResumeService,
)


@dataclass(frozen=True)
class ApprovalPrincipal:
    """
    已经过服务端身份认证的用户上下文。

    不能直接从前端 JSON 构造。
    """
    user_id: str
    roles: frozenset[str]


class ApprovalPermissionError(PermissionError):
    pass


class SecureApprovalService:
    """
    工作流安全审批服务。

    功能：
    - 检查服务端身份和角色
    - PostgreSQL 审批行锁
    - LangGraph Resume
    - 审批状态和审计记录

    仅用于当前只读分析工作流。
    """

    def __init__(
        self,
        workflow: Any,
        store: ApprovalStore,
    ):
        self.workflow = workflow
        self.store = store

        self.resume_service = WorkflowResumeService(
            workflow
        )

    @staticmethod
    def authorize(principal: ApprovalPrincipal) -> None:
        """
        当前版本采用固定角色验证。

        V4.8 需要再增加资源级权限：
        哪个用户可以审批哪个设备/产线的任务。
        """

        if not principal.user_id.strip():
            raise ApprovalPermissionError(
                "缺少认证用户"
            )

        if "workflow_approver" not in principal.roles:
            raise ApprovalPermissionError(
                "当前用户无审批权限"
            )

    def register_pending(
        self,
        thread_id: str,
    ):
        """
        工作流真正进入 interrupt 后注册审批记录。
        """

        pending = self.resume_service.get_pending_approval(
            thread_id
        )

        return self.store.register_pending(
            thread_id=thread_id,
            workflow_id=pending["workflow_id"],
        )

    def approve_or_reject(
        self,
        *,
        thread_id: str,
        workflow_id: str,
        approved: bool,
        principal: ApprovalPrincipal,
    ) -> dict:
        """
        同一个数据库事务内：

        1. 校验身份角色
        2. 锁住审批行
        3. 再次检查 LangGraph 待审批状态
        4. 恢复执行
        5. 保存审批记录与审计
        """

        self.authorize(principal)

        if type(approved) is not bool:
            raise ValueError(
                "approved 必须为布尔值"
            )

        with self.store.connect() as conn:

            # SELECT FOR UPDATE
            self.store.lock_pending(
                conn,
                thread_id=thread_id,
                workflow_id=workflow_id,
            )

            # 在持锁期间重新检查 Checkpoint
            pending = (
                self.resume_service.get_pending_approval(
                    thread_id
                )
            )

            if pending["workflow_id"] != workflow_id:
                raise ValueError(
                    "审批工作流标识不匹配"
                )

            # 恢复执行 LangGraph
            result = self.resume_service.resume(
                thread_id=thread_id,
                workflow_id=workflow_id,
                approved=approved,
            )

            # 成功到达终态后写入审批决定
            self.store.record_decision(
                conn,
                thread_id=thread_id,
                workflow_id=workflow_id,
                actor_id=principal.user_id,
                approved=approved,
            )

            # with 正常结束时提交事务
            return result
