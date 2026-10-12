import sqlglot
from sqlglot import exp

from agent.sql.policies import (
    READ_ONLY_ALLOWED_TABLES,
)
from agent.sql.schemas import SQLValidationResult


class SQLValidator:
    """
    SQL 安全校验器。

    职责：
    - SQL 语法解析
    - 禁止多语句
    - 只允许查询语句
    - 检查表白名单
    - 禁止危险 SQL

    不负责：
    - SQL 生成
    - SQL 执行
    """

    def __init__(
        self,
        allowed_tables: set[str] | None = None,
    ):
        self.allowed_tables = (
            allowed_tables
            or READ_ONLY_ALLOWED_TABLES
        )

    def validate(
        self,
        sql: str,
    ) -> SQLValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not sql or not sql.strip():
            return SQLValidationResult(
                is_valid=False,
                errors=["SQL cannot be empty."],
            )

        # 1. SQL AST 解析
        try:
            statements = sqlglot.parse(
                sql,
                read="postgres",
            )
        except Exception as exc:
            return SQLValidationResult(
                is_valid=False,
                errors=[
                    f"Invalid SQL syntax: {exc}"
                ],
            )

        # 2. 禁止一次执行多条 SQL
        if len(statements) != 1:
            return SQLValidationResult(
                is_valid=False,
                errors=[
                    "Multiple SQL statements are not allowed."
                ],
            )

        statement = statements[0]

        # 3. 只允许查询类 SQL
        self._validate_read_only(
            statement,
            errors,
        )

        # 4. 校验访问的表
        self._validate_tables(
            statement,
            errors,
        )

        return SQLValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_read_only(
        self,
        statement: exp.Expression,
        errors: list[str],
    ) -> None:
        """
        禁止所有数据库写操作。
        """

        blocked_types = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Alter,
            exp.Create,
        )

        for blocked_type in blocked_types:
            if statement.find(blocked_type):
                errors.append(
                    f"{blocked_type.__name__.upper()} "
                    "statements are not allowed."
                )

        # 根节点也必须是查询类型
        if not isinstance(  # noqa: SIM102
            statement,
            (
                exp.Select,
                exp.Union,
                exp.Intersect,
                exp.Except,
            ),
        ):
            # WITH ... SELECT 的情况底层可能仍可解析为 Select
            if not statement.find(exp.Select):
                errors.append(
                    "Only read-only SELECT queries are allowed."
                )

    def _validate_tables(
        self,
        statement: exp.Expression,
        errors: list[str],
    ) -> None:
        """
        SQL 只能访问白名单中的业务表。
        """

        tables = {
            table.name
            for table in statement.find_all(exp.Table)
        }

        unauthorized_tables = (
            tables - self.allowed_tables
        )

        if unauthorized_tables:
            errors.append(
                "Unauthorized tables: "
                + ", ".join(
                    sorted(unauthorized_tables)
                )
            )