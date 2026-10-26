import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

dsn = os.environ["TEST_APPROVAL_DSN"]

with psycopg.connect(dsn) as conn:
    rows = conn.execute(
        """
        SELECT
            to_regclass('workflow_approvals'),
            to_regclass('workflow_approval_audit')
        """
    ).fetchone()

    print("审批状态表：", rows[0])
    print("审批审计表：", rows[1])
