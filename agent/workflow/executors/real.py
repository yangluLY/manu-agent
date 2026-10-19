
from typing import Callable  # noqa: UP035

from agent.workflow.schemas.plan import PlanStep
from agent.workflow.schemas.result import AgentOutput

AgentRunner = Callable[
    [PlanStep, list[dict]],
    str | AgentOutput,
]


class RealStepRunner:
    """
    真实 MES / RAG / BI / Summary 执行分发器。
    """

    def __init__(
        self,
        *,
        mes_runner: AgentRunner,
        rag_runner: AgentRunner,
        bi_runner: AgentRunner,
        summary_runner: AgentRunner,
    ):
        self.runners = {
            "mes": mes_runner,
            "rag": rag_runner,
            "bi": bi_runner,
            "summary": summary_runner,
        }

    def __call__(
        self,
        step: PlanStep,
        previous_results: list[dict],
    ) -> str | AgentOutput:

        runner = self.runners.get(step.agent)

        if runner is None:
            raise ValueError(
                f"不支持的 Agent 类型: {step.agent}"
            )

        return runner(
            step,
            previous_results,
        )
