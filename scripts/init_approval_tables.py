
"""
初始化 ManuAgent 审批业务表。

运行：
python -m scripts.init_approval_tables
"""

import psycopg

from agent.workflow.persistence.postgres import (
    get_checkpoint_dsn,
)

DDL = """
CREATE TABLE IF NOT EXISTS workflow_approvals (
    id BIGSERIAL PRIMARY KEY,

    thread_id TEXT NOT NULL UNIQUE,
    workflow_id TEXT NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    approved BOOLEAN,
    approver_id TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMPTZ,

    CONSTRAINT workflow_approval_status_check
    CHECK (status IN ('pending', 'consumed'))
);

CREATE TABLE IF NOT EXISTS workflow_approval_audit (
    id BIGSERIAL PRIMARY KEY,

    thread_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,

    actor_id TEXT NOT NULL,
    decision VARCHAR(20) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT workflow_audit_decision_check
    CHECK (decision IN ('approved', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_workflow_approval_audit_thread
ON workflow_approval_audit(thread_id);
"""


def main():
    dsn = get_checkpoint_dsn()

    with psycopg.connect(dsn) as conn:
        conn.execute(DDL)

    print("审批业务表初始化成功")


if __name__ == "__main__":
    main()
