import time

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from agent.sql.errors import (
    SQLExecutionError,
    SQLValidationError,
)
from agent.sql.policies import (
    ABSOLUTE_MAX_ROWS,
    DEFAULT_MAX_ROWS,
    DEFAULT_QUERY_TIMEOUT_MS,
)
from agent.sql.schemas import QueryResult
from agent.sql.validator import SQLValidator


class SQLExecutor:
    """
    只读 SQL 执行器。

    职责：
    - 执行经过安全校验的 SQL
    - 设置 PostgreSQL Read Only Transaction
    - 设置 Query Timeout
    - 限制返回结果数量
    - 统一 QueryResult

    不负责：
    - SQL 生成
    - SQL 修正
    - 数据分析
    """

    def __init__(
        self,
        engine: Engine,
        validator: SQLValidator,
        max_rows: int = DEFAULT_MAX_ROWS,
        timeout_ms: int = DEFAULT_QUERY_TIMEOUT_MS,
    ):
        self.engine = engine
        self.validator = validator

        self.max_rows = min(
            max_rows,
            ABSOLUTE_MAX_ROWS,
        )

        self.timeout_ms = timeout_ms

    def execute(
        self,
        sql: str,
    ) -> QueryResult:
        """
        校验并执行只读 SQL。
        """

        validation = self.validator.validate(sql)

        if not validation.is_valid:
            raise SQLValidationError(
                "; ".join(validation.errors)
            )

        started_at = time.perf_counter()

        try:
            result = self._execute_query(sql)

        except SQLAlchemyError as exc:
            raise SQLExecutionError(
                f"SQL execution failed: {exc}"
            ) from exc

        execution_time_ms = (
            time.perf_counter() - started_at
        ) * 1000

        result.execution_time_ms = round(
            execution_time_ms,
            2,
        )

        return result

    def _execute_query(
        self,
        sql: str,
    ) -> QueryResult:
        with self.engine.connect() as connection, connection.begin():

            # PostgreSQL：
            # 当前事务强制设置为只读
            connection.execute(
                text(
                    "SET TRANSACTION READ ONLY"
                )
            )

            # PostgreSQL：
            # 当前事务设置 SQL 超时
            connection.execute(
                text(
                    "SET LOCAL statement_timeout "
                    f"= '{self.timeout_ms}ms'"
                )
            )

            result = connection.execute(
                text(sql)
            )

            columns = list(result.keys())

            # 多取一条，用于判断是否发生截断
            raw_rows = result.fetchmany(
                self.max_rows + 1
            )

            truncated = (
                len(raw_rows) > self.max_rows
            )

            raw_rows = raw_rows[
                :self.max_rows
            ]

            rows = [
                dict(row._mapping)
                for row in raw_rows
            ]

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
            )