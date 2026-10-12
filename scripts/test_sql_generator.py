from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.generator import SQLGenerator
from agent.sql.schema_provider import SchemaProvider
from services.database.session import engine


def main() -> None:
    schema_provider = SchemaProvider(
        engine=engine,
    )

    llm = DeepSeekClient()

    generator = SQLGenerator(
        llm=llm,
        schema_provider=schema_provider,
    )

    questions = [
        "查询所有设备的编号、名称和状态",
        "查询最近10条报警记录",
        "统计每台设备的报警次数",
        "查询报警次数最多的5台设备",
    ]

    for question in questions:
        print("\n")
        print("=" * 70)
        print(f"Question: {question}")
        print("=" * 70)

        result = generator.generate(question)

        print("\nSQL:")
        print(result.sql)

        print("\nExplanation:")
        print(result.explanation)

        print("\nTables:")
        print(result.tables)


if __name__ == "__main__":
    main()