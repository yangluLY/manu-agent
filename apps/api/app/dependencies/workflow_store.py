
from agent.workflow.persistence.thread_store import (
    WorkflowThreadStore,
)


def get_thread_store() -> WorkflowThreadStore:
    """
    FastAPI Workflow 归属管理依赖。

    用于：
    1. 创建工作流时登记 owner_id
    2. 查询历史时检查所有者
    3. 审批时检查访问权限
    """
    return WorkflowThreadStore()
