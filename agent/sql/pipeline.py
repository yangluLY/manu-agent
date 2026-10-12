from agent.sql.corrector import SQLCorrector
from agent.sql.errors import (
    SQLExecutionError,
    SQLRetryExhaustedError,
    SQLValidationError,
)
from agent.sql.executor import SQLExecutor
from agent.sql.generator import SQLGenerator
from agent.sql.schemas import (
    SQLAttempt,
    SQLPipelineResult,
)


class SQLPipeline:
    """
    SQL Agent 执行管线。

    流程：

    Natural Language
        ↓
    SQL Generator
        ↓
    SQL Executor
        ↓
    Failed?
        ↓
    SQL Corrector
        ↓
    Retry

    SQLExecutor 内部负责安全校验。
    """

    def __init__(
        self,
        generator: SQLGenerator,
        corrector: SQLCorrector,
        executor: SQLExecutor,
        max_retries: int = 2,
    ):
        self.generator = generator
        self.corrector = corrector
        self.executor = executor
        self.max_retries = max_retries

    def run(
        self,
        question: str,
    ) -> SQLPipelineResult:

        generated = self.generator.generate(
            question
        )

        current_sql = generated.sql

        attempts: list[SQLAttempt] = []

        # 第一次执行 + max_retries
        total_attempts = (
            self.max_retries + 1
        )

        for attempt_number in range(
            1,
            total_attempts + 1,
        ):
            try:
                result = self.executor.execute(
                    current_sql
                )

                attempts.append(
                    SQLAttempt(
                        attempt=attempt_number,
                        sql=current_sql,
                        error=None,
                        corrected=attempt_number > 1,
                    )
                )

                return SQLPipelineResult(
                    question=question,
                    sql=current_sql,
                    data=result,
                    attempts=attempts,
                    retry_count=attempt_number - 1,
                )

            except SQLValidationError:
                # 安全校验失败绝对不能自动绕过。
                raise

            except SQLExecutionError as exc:
                error_message = str(exc)

                attempts.append(
                    SQLAttempt(
                        attempt=attempt_number,
                        sql=current_sql,
                        error=error_message,
                        corrected=attempt_number > 1,
                    )
                )

                # 已经没有重试次数
                if (
                    attempt_number
                    >= total_attempts
                ):
                    raise SQLRetryExhaustedError(
                        "SQL execution failed "
                        f"after {attempt_number} "
                        "attempts. "
                        f"Last error: {error_message}"
                    ) from exc

                correction = (
                    self.corrector.correct(
                        question=question,
                        failed_sql=current_sql,
                        error_message=error_message,
                    )
                )

                current_sql = correction.sql

        raise SQLRetryExhaustedError(
            "SQL retry exhausted."
        )