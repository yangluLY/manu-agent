
import json
from typing import Callable  # noqa: UP035

from agent.workflow.prompts.planner_prompt import (
    PLANNER_SYSTEM_PROMPT,
)
from agent.workflow.schemas.plan import ExecutionPlan
from agent.workflow.state import WorkflowState


def parse_plan(content: str) -> ExecutionPlan:
    """
    解析并验证 LLM 生成的执行计划。
    """

    data = json.loads(content)

    return ExecutionPlan.model_validate(data)


def create_planner_node(
    llm_invoke: Callable[[str, str], str],
):
    """
    创建 Planner Node。

    llm_invoke:
        system_prompt, user_input -> str
    """

    def planner_node(
        state: WorkflowState,
    ) -> dict:

        content = llm_invoke(
            PLANNER_SYSTEM_PROMPT,
            state["user_input"],
        )

        execution_plan = parse_plan(content)

        return {
             "plan": execution_plan.steps,
             "current_step": 0,
             "step_results": [],
             "result": "",
        }

    return planner_node
