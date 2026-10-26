
from collections.abc import Iterator

from agent.workflow.factory import (
    get_persistent_real_workflow,
)
from agent.workflow.persistence.postgres import (
    get_postgres_checkpointer,
)
from services.database.session import SessionLocal


def get_workflow_runtime() -> Iterator:
    """
    FastAPI Workflow 依赖。

    在一个请求生命周期内保持：
    1. MES 数据库 Session
    2. PostgreSQL Checkpointer
    3. 已编译工作流

    请求结束后自动释放数据库资源。
    """

    with SessionLocal() as db, get_postgres_checkpointer() as saver:

        workflow = get_persistent_real_workflow(
            db=db,
            checkpointer=saver,
        )

        yield workflow
