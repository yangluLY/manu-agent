
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.orm import Session

from agent.llm.deepseek_client import DeepSeekClient
from agent.workflow.executors.factory import (
    create_real_step_runner,
)
from agent.workflow.graph import build_workflow


def create_deepseek_invoke(
    llm: DeepSeekClient,
):
    """
    将 DeepSeekClient 适配成
    workflow 使用的统一调用接口。
    """

    def llm_invoke(
        system_prompt: str,
        user_input: str,
    ) -> str:

        response = llm.create_response(
            input_items=user_input,
            instructions=system_prompt,
        )

        content = response.output_text

        if not content:
            raise ValueError(
                "DeepSeek 返回空内容"
            )

        return content

    return llm_invoke


def get_workflow(
    llm: DeepSeekClient | None = None,
    step_runner=None,
):
    """
    创建 ManuAgent V4 工作流。

    V4.4.1 默认使用 Mock Executor。
    V4.4.2 可以注入真实 Agent Executor。
    """

    if llm is None:
        llm = DeepSeekClient()

    llm_invoke = create_deepseek_invoke(llm)

    return build_workflow(
        llm_invoke=llm_invoke,
        step_runner=step_runner,
    )


def get_real_workflow(
    db: Session,
):
    """
    创建真实业务 LangGraph 工作流。

    注意：数据库 Session 必须在整个 invoke
    执行期间保持有效。
    """

    llm = DeepSeekClient()

    step_runner = create_real_step_runner(
        db=db,
        llm=llm,
    )

    return get_workflow(
        llm=llm,
        step_runner=step_runner,
    )


def get_persistent_real_workflow(
    db: Session,
    checkpointer: BaseCheckpointSaver,
):
    """
    V4.8 专用真实工作流。

    使用：
    - DeepSeek Router / Planner
    - MES / RAG / BI 真实执行器
    - PostgreSQL Checkpointer

    注意：
    自动调用路径必须启用工具级只读权限。
    """

    llm = DeepSeekClient()

    step_runner = create_real_step_runner(
        db=db,
        llm=llm,
    )

    return build_workflow(
        llm_invoke=create_deepseek_invoke(llm),
        step_runner=step_runner,
        checkpointer=checkpointer,
        require_approval=False,
    )
