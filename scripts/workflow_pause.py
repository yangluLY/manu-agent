
"""
V4.7.4 - 独立进程 A

运行：
python -m scripts.workflow_pause
"""

import json
from uuid import uuid4

from agent.workflow.persistence.approval_store import (
    ApprovalStore,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
    get_postgres_checkpointer,
)
from agent.workflow.persistence.resume_service import (
    WorkflowResumeService,
)
from agent.workflow.persistence.secure_approval import (
    SecureApprovalService,
)
from scripts.workflow_resume_fixture import (
    create_resume_workflow,
    initial_state,
)


def main():

    thread_id = f"v474-{uuid4()}"

    config = build_thread_config(thread_id)

    with get_postgres_checkpointer() as saver:

        workflow = create_resume_workflow(saver)

        result = workflow.invoke(
            initial_state(),
            config=config,
        )

        interrupts = result.get("__interrupt__", ())

        if not interrupts:
            raise RuntimeError(
                "工作流没有进入审批中断状态"
            )

        payload = interrupts[0].value

        service = SecureApprovalService(
            workflow=workflow,
            store=ApprovalStore(),
        )

        record = service.register_pending(thread_id)

        pending = service.resume_service.get_pending_approval(
            thread_id
        )

        assert record.status == "pending"
        assert record.workflow_id == pending["workflow_id"]

        assert (
            pending["workflow_id"]
            == payload["workflow_id"]
        )

        snapshot = workflow.get_state(config)

        assert snapshot.values.get(
            "step_results",
            []
        ) == []

        print("\n=== 工作流暂停成功 ===")

        print(
            json.dumps(
                pending,
                ensure_ascii=False,
                indent=2,
            )
        )

        print("\n请保存以下信息：")
        print("thread_id:", thread_id)
        print(
            "workflow_id:",
            pending["workflow_id"],
        )

        print("\nPython 进程即将结束")

        print(
            "尚未执行业务 Agent，"
            "Checkpoint 已保存到 PostgreSQL。"
        )


if __name__ == "__main__":
    main()
