from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.corrector import SQLCorrector
from agent.sql.schema_provider import SchemaProvider
from services.database.session import engine


def main() -> None:
    schema_provider = SchemaProvider(
        engine=engine,
    )

    corrector = SQLCorrector(
        llm=DeepSeekClient(),
        schema_provider=schema_provider,
    )

    result = corrector.correct(
        question="查询所有设备名称",
        failed_sql="""
        SELECT
            m.code,
            COUNT(a.id)
        FROM machines m
        JOIN machine_alarms a
            ON a.machine_code = m.code
        GROUP BY m.code;
        """,
        error_message="""
        column "name" does not exist
        """,
    )

    print("Corrected SQL:")
    print(result.sql)

    print("\nExplanation:")
    print(result.explanation)

    print("\nTables:")
    print(result.tables)


if __name__ == "__main__":
    main()