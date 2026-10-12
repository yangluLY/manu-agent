from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.generator import SQLGenerator
from agent.sql.schema_provider import SchemaProvider
from agent.sql.validator import SQLValidator
from services.database.session import engine


def main() -> None:
    schema_provider = SchemaProvider(
        engine=engine,
    )

    generator = SQLGenerator(
        llm=DeepSeekClient(),
        schema_provider=schema_provider,
    )

    validator = SQLValidator()

    question = "统计每台设备的报警次数"

    # 1. 生成 SQL
    generated = generator.generate(question)

    print("=" * 70)
    print("Generated SQL")
    print("=" * 70)

    print(generated.sql)

    # 2. 校验 SQL
    validation = validator.validate(
        generated.sql
    )

    print("\n")
    print("=" * 70)
    print("Validation")
    print("=" * 70)

    print(
        f"Valid: {validation.is_valid}"
    )

    if validation.errors:
        for error in validation.errors:
            print(f"- {error}")


if __name__ == "__main__":
    main()