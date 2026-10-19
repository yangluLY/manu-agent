import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

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
        校验 SQL 实际访问的物理表。

        支持：
        - 普通 SELECT
        - JOIN
        - CTE (WITH ... AS)
        - 子查询

        CTE 名称不需要加入表白名单。
        """

        physical_tables: set[str] = set()

        # 基于 SQLGlot 的 Scope 分析真实数据来源
        for scope in traverse_scope(statement):

            for _, source in scope.selected_sources.values():

                if isinstance(source, exp.Table):
                    physical_tables.add(
                        source.name.lower()
                    )

        # 表白名单统一为小写
        allowed_tables = {
            name.lower()
            for name in self.allowed_tables
        }

        unauthorized_tables = (
            physical_tables - allowed_tables
        )

        if unauthorized_tables:
            errors.append(
                "Unauthorized tables: "
                + ", ".join(
                    sorted(unauthorized_tables)
                )
            )
