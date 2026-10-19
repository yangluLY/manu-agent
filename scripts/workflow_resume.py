
"""
V4.7.4 - 独立进程 B

运行：

python -m scripts.workflow_resume \
    --thread-id THREAD_ID \
    --workflow-id WORKFLOW_ID \
    --decision approve

Windows PowerShell 建议写成单行。
"""

import argparse

from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)
from agent.workflow.persistence.postgres import (
    get_postgres_checkpointer,
)
from agent.workflow.persistence.resume_service import (
    WorkflowResumeService,
)
from scripts.workflow_resume_fixture import (
    create_resume_workflow,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="恢复 ManuAgent 工作流"
    )

    parser.add_argument(
        "--thread-id",
        required=True,
    )

    parser.add_argument(
        "--workflow-id",
        required=True,
    )

    parser.add_argument(
        "--decision",
        choices=["approve", "reject"],
        required=True,
    )

    return parser.parse_args()


def main():

    args = parse_args()

    approved = args.decision == "approve"

    with get_postgres_checkpointer() as saver:

        workflow = create_resume_workflow(saver)

        service = WorkflowResumeService(
            workflow
        )

        print("\n=== 恢复工作流 ===")
        print("Thread ID:", args.thread_id)
        print("Workflow ID:", args.workflow_id)
        print("Approval:", approved)

        result = service.resume(
            thread_id=args.thread_id,
            workflow_id=args.workflow_id,
            approved=approved,
        )

        response = build_workflow_response(
            result
        )

        print("\n=== WorkflowResponse ===")

        print(
            response.model_dump_json(
                indent=2
            )
        )

        snapshot = workflow.get_state(
            {
                "configurable": {
                    "thread_id": args.thread_id,
                }
            }
        )

        assert not snapshot.next

        if approved:
            assert response.status == "completed"
            assert len(response.steps) == 1
        else:
            assert response.status == "failed"
            assert response.steps == []

        print("\n跨进程工作流恢复测试通过")


if __name__ == "__main__":
    main()
