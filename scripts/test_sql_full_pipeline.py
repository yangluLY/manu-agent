from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.executor import SQLExecutor
from agent.sql.generator import SQLGenerator
from agent.sql.schema_provider import SchemaProvider
from agent.sql.validator import SQLValidator
from services.database.session import engine


def main() -> None:
    # 1. Schema
    schema_provider = SchemaProvider(
        engine=engine,
    )

    # 2. LLM
    llm = DeepSeekClient()

    # 3. Generator
    generator = SQLGenerator(
        llm=llm,
        schema_provider=schema_provider,
    )

    # 4. Validator
    validator = SQLValidator()

    # 5. Executor
    executor = SQLExecutor(
        engine=engine,
        validator=validator,
    )

    question = "查询库存数量最低的5种物料"
    # 查询所有设备的编号、名称和状态
    # 查询最近10条报警记录
    # 统计每台设备的报警次数
    # 查询报警次数最多的5台设备
    # 查询库存数量最低的5种物料

    print("=" * 70)
    print("Question")
    print("=" * 70)

    print(question)

    # Natural Language -> SQL
    generated = generator.generate(
        question
    )

    print("\nGenerated SQL:")
    print(generated.sql)

    # SQL -> PostgreSQL
    result = executor.execute(
        generated.sql
    )

    print("\nResult:")

    for row in result.rows:
        print(row)

    print(
        f"\nRows: {result.row_count}"
    )

    print(
        f"Execution: "
        f"{result.execution_time_ms} ms"
    )


if __name__ == "__main__":
    main()