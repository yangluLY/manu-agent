
from collections.abc import Callable
from time import perf_counter

from agent.workflow.executors.retry_policy import (
    RetryPolicy,
    classify_error,
)
from agent.workflow.schemas.execution import ExecutionEvent
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

    if isinstance(value, AgentOutput):
        return value

    if isinstance(value, str):
        return AgentOutput(output=value)

    if isinstance(value, dict):
        return AgentOutput.model_validate(value)

    raise TypeError(
        "不支持的 Agent 输出类型"
    )


def create_step_executor_node(
    step_runner: StepRunner,
    retry_policy: RetryPolicy | None = None,
):
    """
    执行当前 PlanStep。

    V4.6:
    - 捕获执行异常
    - 仅对允许的异常重试
    - 记录重试事件
    - 保存成功或失败结果
    """

    policy = retry_policy or RetryPolicy()

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

        previous_results = list(
            state.get("step_results", [])
        )

        events = list(
            state.get("execution_events", [])
        )

        start = perf_counter()
        attempts = 0

        while True:
            attempts += 1

            try:
                raw_output = step_runner(
                    step,
                    previous_results,
                )

                agent_output = normalize_agent_output(
                    raw_output
                )

                duration_ms = round(
                    (perf_counter() - start) * 1000,
                    2,
                )

                step_result = {
                    "step_id": step.id,
                    "agent": step.agent,
                    "task": step.task,
                    "status": "success",
                    "duration_ms": duration_ms,
                    "attempts": attempts,
                    **agent_output.model_dump(
                        mode="json"
                    ),
                }

                events.append(
                    ExecutionEvent(
                        event_type="step_completed",
                        step_id=step.id,
                        agent=step.agent,
                        duration_ms=duration_ms,
                        details={
                            "status": "success",
                            "attempts": attempts,
                        },
                    ).model_dump(mode="json")
                )

                return {
                    "current_step": current_step + 1,
                    "step_results": [
                        *previous_results,
                        step_result,
                    ],
                    "execution_events": events,
                    "result": agent_output.output,
                }

            except Exception as exc:
                # 不捕获 KeyboardInterrupt/SystemExit

                retryable = policy.should_retry(exc)

                if (
                    retryable
                    and attempts <= policy.max_retries
                ):
                    events.append(
                        ExecutionEvent(
                            event_type="step_retry",
                            step_id=step.id,
                            agent=step.agent,
                            details={
                                "attempt": attempts,
                                "next_attempt": attempts + 1,
                            },
                        ).model_dump(mode="json")
                    )

                    policy.wait(attempts)
                    continue

                error = classify_error(
                    exc=exc,
                    attempts=attempts,
                    policy=policy,
                )

                duration_ms = round(
                    (perf_counter() - start) * 1000,
                    2,
                )

                failure_text = (
                    f"{step.agent.upper()} "
                    f"步骤执行失败：{error.message}"
                )

                step_result = {
                    "step_id": step.id,
                    "agent": step.agent,
                    "task": step.task,
                    "status": "failed",
                    "duration_ms": duration_ms,
                    "attempts": attempts,
                    "error": error.model_dump(
                        mode="json"
                    ),
                    "output": failure_text,
                    "data": None,
                    "sources": [],
                    "sql": None,
                    "chart": None,
                }

                events.append(
                    ExecutionEvent(
                        event_type="step_failed",
                        step_id=step.id,
                        agent=step.agent,
                        duration_ms=duration_ms,
                        details={
                            "error_code": error.code,
                            "attempts": attempts,
                        },
                    ).model_dump(mode="json")
                )

                return {
                    "current_step": current_step + 1,
                    "step_results": [
                        *previous_results,
                        step_result,
                    ],
                    "execution_events": events,
                    "result": failure_text,
                }

    return step_executor_node
