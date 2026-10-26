
"""
初始化 ManuAgent 审批测试表。

执行：
python -m scripts.init_workflow_approvals

只使用 TEST_APPROVAL_DSN，
避免误操作正式业务数据库。
"""

import os

from dotenv import load_dotenv

from agent.workflow.persistence.approval_store import (
    ApprovalStore,
)


def main():
    load_dotenv()

    test_dsn = os.getenv("TEST_APPROVAL_DSN")

    if not test_dsn:
        raise RuntimeError(
            "未配置 TEST_APPROVAL_DSN"
        )

    store = ApprovalStore(dsn=test_dsn)

    # 确认连接到的是独立测试库
    with store.connect() as conn:
        database_name = conn.execute(
            "SELECT current_database()"
        ).fetchone()[0]

    if not database_name.endswith("_test"):
        raise RuntimeError(
            f"拒绝初始化非测试数据库：{database_name}"
        )

    store.setup()

    print(
        f"审批测试表初始化成功：{database_name}"
    )


if __name__ == "__main__":
    main()
