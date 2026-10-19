
from typing import Any

from agent.workflow.persistence.postgres import (
    build_thread_config,
)
from agent.workflow.schemas.checkpoint import (
    CheckpointSummary,
    WorkflowHistoryResponse,
    WorkflowStateDetail,
)

VALID_STATUSES = {
    "pending",
    "running",
    "completed",
    "partial",
    "failed",
}


class WorkflowHistoryService:
    """
    ManuAgent V4.7.2

    读取 LangGraph Checkpoint 历史。
    不执行 Agent，不修改业务状态。
    """

    def __init__(self, workflow: Any):
        self.workflow = workflow

    @staticmethod
    def _require_id(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} 不能为空")
        return value.strip()

    @staticmethod
    def _checkpoint_id(config: dict | None) -> str | None:
        if not config:
            return None

        return config.get(
            "configurable", {}
        ).get("checkpoint_id")

    @staticmethod
    def _to_summary(
        snapshot: Any,
        thread_id: str,
    ) -> CheckpointSummary:
        values = snapshot.values or {}
        metadata = snapshot.metadata or {}

        checkpoint_id = (
            WorkflowHistoryService._checkpoint_id(
                snapshot.config
            )
        )

        if not checkpoint_id:
            raise ValueError(
                "Checkpoint 缺少 checkpoint_id"
            )

        status = values.get(
            "workflow_status",
            "unknown",
        )

        if status not in VALID_STATUSES:
            status = "unknown"

        step_results = values.get(
            "step_results",
            [],
        ) or []

        completed_steps = sum(
            1
            for item in step_results
            if isinstance(item, dict)
            and item.get("status") == "success"
        )

        return CheckpointSummary(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            parent_checkpoint_id=(
                WorkflowHistoryService._checkpoint_id(
                    snapshot.parent_config
                )
            ),
            created_at=snapshot.created_at,
            source=metadata.get("source"),
            step=metadata.get("step"),
            next_nodes=list(snapshot.next or ()),
            workflow_id=values.get("workflow_id"),
            workflow_status=status,
            route=values.get("route"),
            completed_steps=completed_steps,
        )

    def list_workflow_history(
        self,
        thread_id: str,
        limit: int = 20,
    ) -> WorkflowHistoryResponse:
        """
        查询指定线程的最近若干条检查点。
        最新的检查点排在最前面。
        """

        thread_id = self._require_id(
            thread_id,
            "thread_id",
        )

        if not 1 <= limit <= 100:
            raise ValueError(
                "limit 必须在 1 到 100 之间"
            )

        config = build_thread_config(thread_id)

        snapshots = self.workflow.get_state_history(
            config,
            limit=limit,
        )

        checkpoints = [
            self._to_summary(snapshot, thread_id)
            for snapshot in snapshots
        ]

        return WorkflowHistoryResponse(
            thread_id=thread_id,
            total=len(checkpoints),
            checkpoints=checkpoints,
        )
    

    def get_workflow_state(
        self,
        thread_id: str,
    ) -> WorkflowStateDetail | None:
        """
        读取当前线程最新的 Checkpoint。

        即使 State 为空，也允许返回有效 Checkpoint。
        """

        thread_id = self._require_id(
            thread_id,
            "thread_id",
        )

        config = build_thread_config(thread_id)

        snapshot = self.workflow.get_state(config)

        checkpoint_id = self._checkpoint_id(
            snapshot.config
        )

        if not checkpoint_id:
            return None

        return self._to_detail(
            snapshot,
            thread_id,
        )

    
    def get_checkpoint_state(
        self,
        thread_id: str,
        checkpoint_id: str,
    ) -> WorkflowStateDetail | None:
        """
        根据 checkpoint_id 精确查询历史状态。

        注意：
        初始 Checkpoint 的 values 可能为空字典，
        不能将其判断为不存在。
        """

        thread_id = self._require_id(
            thread_id,
            "thread_id",
        )

        checkpoint_id = self._require_id(
            checkpoint_id,
            "checkpoint_id",
        )

        config = build_thread_config(thread_id)

        config["configurable"]["checkpoint_id"] = (
            checkpoint_id
        )

        snapshot = self.workflow.get_state(config)

        # 根据实际 checkpoint_id 判断是否找到
        actual_id = self._checkpoint_id(
            snapshot.config
        )

        if actual_id != checkpoint_id:
            return None

        return self._to_detail(
            snapshot,
            thread_id,
        )


    def _to_detail(
        self,
        snapshot: Any,
        thread_id: str,
    ) -> WorkflowStateDetail:
        """
        转换业务详情。

        仅返回步骤摘要、事件类型及最终回答。
        不暴露原始模型上下文或完整 SQL。
        """

        values = snapshot.values or {}

        executed_steps = []

        for step in values.get(
            "step_results",
            [],
        ) or []:
            if not isinstance(step, dict):
                continue

            executed_steps.append({
                "step_id": step.get("step_id"),
                "agent": step.get("agent"),
                "status": step.get("status"),
                "duration_ms": step.get("duration_ms"),
                "attempts": step.get("attempts", 1),
            })

        execution_events = []

        for event in values.get(
            "execution_events",
            [],
        ) or []:
            if not isinstance(event, dict):
                continue

            execution_events.append({
                "event_type": event.get("event_type"),
                "step_id": event.get("step_id"),
                "agent": event.get("agent"),
                "timestamp": event.get("timestamp"),
                "duration_ms": event.get("duration_ms"),
            })

        return WorkflowStateDetail(
            checkpoint=self._to_summary(
                snapshot,
                thread_id,
            ),
            final_answer=values.get("final_answer") or None,
            executed_steps=executed_steps,
            execution_events=execution_events,
        )
