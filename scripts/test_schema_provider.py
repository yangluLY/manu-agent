from agent.sql.schema_provider import SchemaProvider
from services.database.session import engine

ALLOWED_TABLES = {
    "machines",
    "machine_alarms",
    "work_orders",
    "materials",
    "production_records",
    "knowledge_documents",
    "knowledge_chunks",
}


def main() -> None:
    provider = SchemaProvider(
        engine=engine,
        allowed_tables=ALLOWED_TABLES,
    )

    schema = provider.get_schema()

    print("=" * 60)
    print("DATABASE SCHEMA")
    print("=" * 60)

    for table in schema.tables:
        print(f"\nTable: {table.name}")

        for column in table.columns:
            print(
                f"  {column.name:<25}"
                f"{column.data_type:<25}"
                f"PK={column.primary_key} "
                f"Nullable={column.nullable}"
            )

        if table.foreign_keys:
            print("  Foreign Keys:")

            for fk in table.foreign_keys:
                print(
                    f"    {table.name}.{fk.column}"
                    f" -> "
                    f"{fk.referenced_table}."
                    f"{fk.referenced_column}"
                )

    print("\n")
    print("=" * 60)
    print("LLM PROMPT SCHEMA")
    print("=" * 60)

    print(provider.to_prompt_text())


if __name__ == "__main__":
    main()