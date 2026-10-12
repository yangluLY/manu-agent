class SQLExecutorError(Exception):
    """SQL Executor 基础异常。"""


class SQLExecutionError(SQLExecutorError):
    """SQL 执行失败。"""


class SQLValidationError(SQLExecutorError):
    """SQL 安全校验失败。"""
    

class SQLRetryExhaustedError(
    SQLExecutorError
):
    """SQL 重试次数耗尽。"""