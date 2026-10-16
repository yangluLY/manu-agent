
from typing import Callable  # noqa: UP035

from agent.workflow.schemas.plan import PlanStep
from agent.workflow.schemas.result import AgentOutput
from agent.workflow.state import WorkflowState

StepRunner = Callable[
    [PlanStep, list[dict]],
    str | AgentOutput | dict,
]


def normalize_agent_output(
    value: str | AgentOutput | dict,
) -> AgentOutput:
    """
    统一规范化执行器输出。

    兼容旧 Mock Runner 返回字符串。
    """

    if isinstance(value, AgentOutput):
        return value

    if isinstance(value, str):
        return AgentOutput(output=value)

    if isinstance(value, dict):
        return AgentOutput.model_validate(value)

    raise TypeError(
        f"不支持的执行器输出类型: {type(value)}"
    )


def create_step_executor_node(
    step_runner: StepRunner,
):

    def step_executor_node(
        state: WorkflowState,
    ) -> dict:

        plan = state["plan"]
        current_step = state["current_step"]

        if not 0 <= current_step < len(plan):
            raise ValueError(
                "当前步骤超出执行计划"
            )

        step = plan[current_step]

        previous_results = state.get(
            "step_results",
            [],
        )

        # 1. 调用业务 Agent
        raw_output = step_runner(
            step,
            previous_results,
        )

        # 2. 标准化
        agent_output = normalize_agent_output(
            raw_output
        )

        # 3. 构建完整执行记录
        step_result = {
            "step_id": step.id,
            "agent": step.agent,
            "task": step.task,
            "status": "success",

            **agent_output.model_dump(mode="json"),
        }

        # 4. 更新 LangGraph State
        return {
            "current_step": current_step + 1,
            "step_results": [
                *previous_results,
                step_result,
            ],
            "result": agent_output.output,
        }

    return step_executor_node
