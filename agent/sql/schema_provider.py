from sqlalchemy import Engine, Inspector, inspect

from agent.sql.schemas import (
    ColumnSchema,
    DatabaseSchema,
    ForeignKeySchema,
    TableSchema,
)


class SchemaProvider:
    def __init__(
        self,
        engine: Engine,
        allowed_tables: set[str] | None = None,
    ):
        self.engine = engine
        self.allowed_tables = allowed_tables

    def get_schema(self) -> DatabaseSchema:
        inspector = inspect(self.engine)

        table_names = inspector.get_table_names()

        if self.allowed_tables:
            table_names = [
                table_name
                for table_name in table_names
                if table_name in self.allowed_tables
            ]

        tables: list[TableSchema] = []

        for table_name in table_names:
            tables.append(
                TableSchema(
                    name=table_name,
                    columns=self._get_columns(
                        inspector,
                        table_name,
                    ),
                    foreign_keys=self._get_foreign_keys(
                        inspector,
                        table_name,
                    ),
                )
            )

        return DatabaseSchema(tables=tables)

    def _get_columns(
        self,
        inspector: Inspector,
        table_name: str,
    ) -> list[ColumnSchema]:
        columns = inspector.get_columns(table_name)

        pk_constraint = inspector.get_pk_constraint(table_name)

        primary_keys = set(
            pk_constraint.get("constrained_columns") or []
        )

        return [
            ColumnSchema(
                name=column["name"],
                data_type=str(column["type"]),
                nullable=column.get("nullable", True),
                primary_key=column["name"] in primary_keys,
            )
            for column in columns
        ]

    def _get_foreign_keys(
        self,
        inspector: Inspector,
        table_name: str,
    ) -> list[ForeignKeySchema]:
        foreign_keys = inspector.get_foreign_keys(table_name)

        result: list[ForeignKeySchema] = []

        for fk in foreign_keys:
            constrained_columns = (
                fk.get("constrained_columns") or []
            )

            referred_columns = (
                fk.get("referred_columns") or []
            )

            referred_table = fk.get("referred_table")

            if not referred_table:
                continue

            for column, referred_column in zip(
                constrained_columns,
                referred_columns,
            ):
                result.append(
                    ForeignKeySchema(
                        column=column,
                        referenced_table=referred_table,
                        referenced_column=referred_column,
                    )
                )

        return result

    def to_prompt_text(self) -> str:
        schema = self.get_schema()

        lines: list[str] = []

        for table in schema.tables:
            lines.append(f"Table: {table.name}")

            for column in table.columns:
                attributes: list[str] = []

                if column.primary_key:
                    attributes.append("PRIMARY KEY")

                if not column.nullable:
                    attributes.append("NOT NULL")

                suffix = ""

                if attributes:
                    suffix = f" {' '.join(attributes)}"

                lines.append(
                    f"- {column.name} "
                    f"{column.data_type}"
                    f"{suffix}"
                )

            if table.foreign_keys:
                lines.append("Relationships:")

                for fk in table.foreign_keys:
                    lines.append(
                        f"- {table.name}.{fk.column}"
                        f" -> "
                        f"{fk.referenced_table}."
                        f"{fk.referenced_column}"
                    )

            lines.append("")

        return "\n".join(lines)