
"""
V4.7.4.3 本地安全审批集成测试。

仅用于开发环境，模拟已认证审批人员。

运行：
python -m scripts.workflow_secure_resume
    --thread-id xxx
    --workflow-id xxx
    --decision approve
"""

import argparse

from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)
from agent.workflow.persistence.approval_store import (
    ApprovalStore,
)
from agent.workflow.persistence.postgres import (
    get_postgres_checkpointer,
)
from agent.workflow.persistence.secure_approval import (
    ApprovalPrincipal,
    SecureApprovalService,
)
from scripts.workflow_resume_fixture import (
    create_resume_workflow,
)


def parse_args():
    parser = argparse.ArgumentParser()

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
        choices=("approve", "reject"),
        required=True,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # 开发脚本模拟服务端已经认证的审批人。
    # 生产环境必须替换成真实身份系统。
    principal = ApprovalPrincipal(
        user_id="local-test-approver",
        roles=frozenset({
            "workflow_approver",
        }),
    )

    with get_postgres_checkpointer() as saver:

        workflow = create_resume_workflow(saver)

        service = SecureApprovalService(
            workflow=workflow,
            store=ApprovalStore(),
        )

        result = service.approve_or_reject(
            thread_id=args.thread_id,
            workflow_id=args.workflow_id,
            approved=args.decision == "approve",
            principal=principal,
        )

        response = build_workflow_response(
            result
        )

        print("\n=== Secure Approval Result ===")
        print(
            response.model_dump_json(
                indent=2
            )
        )

        print("\n审批恢复测试完成")


if __name__ == "__main__":
    main()
