
"""
初始化 LangGraph PostgreSQL Checkpoint 表。

运行：
python -m scripts.init_workflow_checkpoint
"""

from agent.workflow.persistence.postgres import (
    get_postgres_checkpointer,
)


def main():
    print("开始初始化 LangGraph Checkpoint...")

    with get_postgres_checkpointer(
        setup=True
    ):
        print(
            "PostgreSQL Checkpoint 初始化成功"
        )


if __name__ == "__main__":
    main()
