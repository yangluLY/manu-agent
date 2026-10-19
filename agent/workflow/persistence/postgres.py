
"""
ManuAgent V4.7.1

LangGraph PostgreSQL Checkpointer 管理。
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()


def get_checkpoint_dsn() -> str:
    """
    读取 PostgreSQL Checkpoint 连接地址。
    """

    dsn = os.getenv(
        "LANGGRAPH_CHECKPOINT_DSN",
        "",
    ).strip()

    if not dsn:
        raise RuntimeError(
            "缺少环境变量 LANGGRAPH_CHECKPOINT_DSN"
        )

    if not dsn.startswith(
        ("postgresql://", "postgres://")
    ):
        raise ValueError(
            "Checkpoint DSN 必须是 PostgreSQL "
            "连接地址，并使用 psycopg 兼容格式"
        )

    return dsn


@contextmanager
def get_postgres_checkpointer(
    *,
    setup: bool = False,
) -> Iterator[PostgresSaver]:
    """
    创建并管理 PostgresSaver 生命周期。

    首次初始化：
        setup=True

    正常执行：
        setup=False

    必须在 with 作用域内使用 checkpointer。
    """

    dsn = get_checkpoint_dsn()

    with PostgresSaver.from_conn_string(
        dsn
    ) as checkpointer:

        if setup:
            checkpointer.setup()

        yield checkpointer


def build_thread_config(
    thread_id: str,
) -> dict:
    """
    构造 LangGraph thread config。
    """

    if not isinstance(thread_id, str):
        raise TypeError(
            "thread_id 必须是字符串"
        )

    thread_id = thread_id.strip()

    if not thread_id:
        raise ValueError(
            "thread_id 不能为空"
        )

    return {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 30,
    }
