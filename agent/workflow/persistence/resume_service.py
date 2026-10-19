
from typing import Any

from langgraph.types import Command

from agent.workflow.persistence.postgres import (
    build_thread_config,
)


class WorkflowResumeError(Exception):
    """工作流恢复检查失败。"""


class WorkflowResumeService:
    """
    ManuAgent V4.7.4

    在调用 Command(resume=...) 前验证：
    1. thread_id
    2. workflow_id
    3. Checkpoint 是否存在
    4. 是否正在审批节点等待

    注意：
    这里只提供单调用方的状态检查。
    不能代替数据库级并发互斥和幂等控制。
    """

    def __init__(self, workflow: Any):
        self.workflow = workflow

    def get_pending_approval(
        self,
        thread_id: str,
    ) -> dict:
        """
        获取当前待审批的工作流信息。
        """

        config = build_thread_config(thread_id)

        snapshot = self.workflow.get_state(config)

        if not snapshot.config:
            raise WorkflowResumeError(
                "未找到工作流 Checkpoint"
            )

        values = snapshot.values or {}

        workflow_id = values.get("workflow_id")

        if not workflow_id:
            raise WorkflowResumeError(
                "Checkpoint 缺少 workflow_id"
            )

        status = values.get("workflow_status")

        if status in {
            "completed",
            "partial",
            "failed",
        }:
            raise WorkflowResumeError(
                "工作流已经结束，不能再次恢复"
            )

        # LangGraph 中断时，等待执行的节点应为
        # approval_gate
        next_nodes = tuple(snapshot.next or ())

        if next_nodes != ("approval_gate",):
            raise WorkflowResumeError(
                "当前工作流不在人工审批等待状态"
            )

        # 校验实际存在 interrupt 信息，
        # 防止将普通待调度状态误判为审批。
        interrupts = [
            item
            for task in snapshot.tasks
            for item in task.interrupts
        ]

        if not interrupts:
            raise WorkflowResumeError(
                "当前节点没有待处理的 interrupt"
            )

        return {
            "thread_id": thread_id,
            "workflow_id": workflow_id,
            "workflow_status": status,
            "next_nodes": list(next_nodes),
            "interrupt_count": len(interrupts),
        }

    def resume(
        self,
        *,
        thread_id: str,
        workflow_id: str,
        approved: bool,
    ) -> dict:
        """
        恢复等待审批的工作流。
        """

        if not isinstance(workflow_id, str):
            raise WorkflowResumeError(
                "workflow_id 必须是字符串"
            )

        if not workflow_id.strip():
            raise WorkflowResumeError(
                "workflow_id 不能为空"
            )

        if type(approved) is not bool:
            raise WorkflowResumeError(
                "approved 必须是布尔值"
            )

        pending = self.get_pending_approval(
            thread_id
        )

        if pending["workflow_id"] != workflow_id:
            raise WorkflowResumeError(
                "workflow_id 与当前 Checkpoint 不匹配"
            )

        config = build_thread_config(thread_id)

        result = self.workflow.invoke(
            Command(
                resume={
                    "workflow_id": workflow_id,
                    "approved": approved,
                }
            ),
            config=config,
        )

        if "__interrupt__" in result:
            raise WorkflowResumeError(
                "恢复后工作流再次进入中断状态"
            )

        if result.get("workflow_status") not in {
            "completed",
            "partial",
            "failed",
        }:
            raise WorkflowResumeError(
                "恢复后未获得有效的终态"
            )

        return result
