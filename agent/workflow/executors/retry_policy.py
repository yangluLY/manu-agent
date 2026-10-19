
from dataclasses import dataclass
from time import sleep

from agent.sql.errors import SQLValidationError
from agent.workflow.schemas.error import WorkflowError


@dataclass(frozen=True)
class RetryPolicy:
    # 失败后最多额外重试几次
    max_retries: int = 2

    # 首次重试等待时长
    base_delay_seconds: float = 0.2

    # 最大等待时长
    max_delay_seconds: float = 2.0

    def __post_init__(self):
        if self.max_retries < 0:
            raise ValueError("max_retries 不能小于 0")

        if self.base_delay_seconds < 0:
            raise ValueError("等待时间不能小于 0")

        if self.max_delay_seconds < 0:
            raise ValueError("最大等待时间不能小于 0")

    def should_retry(self, exc: Exception) -> bool:
        # 安全和权限错误绝不自动重试
        if isinstance(
            exc,
            (SQLValidationError, PermissionError),
        ):
            return False

        return isinstance(
            exc,
            (TimeoutError, ConnectionError),
        )

    def delay(self, retry_number: int) -> float:
        return min(
            self.base_delay_seconds
            * (2 ** (retry_number - 1)),
            self.max_delay_seconds,
        )

    def wait(self, retry_number: int) -> None:
        seconds = self.delay(retry_number)

        if seconds > 0:
            sleep(seconds)


def classify_error(
    exc: Exception,
    attempts: int,
    policy: RetryPolicy,
) -> WorkflowError:
    """
    转换成不包含内部异常详情的错误对象。
    """

    if isinstance(exc, SQLValidationError):
        return WorkflowError(
            code="SQL_VALIDATION_ERROR",
            message="生成的 SQL 未通过安全校验。",
            retryable=False,
            attempts=attempts,
        )

    if isinstance(exc, PermissionError):
        return WorkflowError(
            code="PERMISSION_DENIED",
            message="当前操作没有执行权限。",
            retryable=False,
            attempts=attempts,
        )

    if isinstance(exc, TimeoutError):
        code = "TIMEOUT"
        message = "下游服务调用超时。"

    elif isinstance(exc, ConnectionError):
        code = "CONNECTION_ERROR"
        message = "下游服务连接失败。"

    elif isinstance(exc, (ValueError, TypeError)):
        code = "INVALID_INPUT"
        message = "执行参数或返回数据不符合要求。"

    else:
        code = "EXECUTION_ERROR"
        message = "Agent 执行发生异常。"

    return WorkflowError(
        code=code,
        message=message,
        retryable=policy.should_retry(exc),
        attempts=attempts,
    )
