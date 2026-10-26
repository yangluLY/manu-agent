
import argparse
import os

import psycopg
from dotenv import load_dotenv

from agent.workflow.persistence.postgres import (
    get_checkpoint_dsn,
)


load_dotenv()


DDL = """
CREATE TABLE IF NOT EXISTS workflow_threads (
    thread_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_threads_owner
ON workflow_threads(owner_id);
"""


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--test",
        action="store_true",
        help="初始化独立测试数据库",
    )

    args = parser.parse_args()

    if args.test:
        dsn = os.getenv("TEST_APPROVAL_DSN")

        if not dsn:
            raise RuntimeError(
                "未配置 TEST_APPROVAL_DSN"
            )
    else:
        dsn = get_checkpoint_dsn()

    with psycopg.connect(dsn) as conn:
        conn.execute(DDL)

    print(
        "测试数据库 workflow_threads 初始化成功"
        if args.test
        else "workflow_threads 初始化成功"
    )


if __name__ == "__main__":
    main()
