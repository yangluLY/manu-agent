from agent.llm.deepseek_client import (
    DeepSeekClient,
)
from agent.sql.corrector import SQLCorrector
from agent.sql.executor import SQLExecutor
from agent.sql.generator import SQLGenerator
from agent.sql.pipeline import SQLPipeline
from agent.sql.schema_provider import (
    SchemaProvider,
)
from agent.sql.validator import SQLValidator
from services.database.session import engine


def main() -> None:
    llm = DeepSeekClient()

    schema_provider = SchemaProvider(
        engine=engine,
    )

    validator = SQLValidator()

    generator = SQLGenerator(
        llm=llm,
        schema_provider=schema_provider,
    )

    corrector = SQLCorrector(
        llm=llm,
        schema_provider=schema_provider,
    )

    executor = SQLExecutor(
        engine=engine,
        validator=validator,
    )

    pipeline = SQLPipeline(
        generator=generator,
        corrector=corrector,
        executor=executor,
        max_retries=2,
    )

    question = (
        "统计每台设备的报警次数"
    )

    result = pipeline.run(question)

    print("=" * 70)
    print("SQL Pipeline")
    print("=" * 70)

    print("\nQuestion:")
    print(result.question)

    print("\nFinal SQL:")
    print(result.sql)

    print("\nRetry Count:")
    print(result.retry_count)

    print("\nAttempts:")

    for attempt in result.attempts:
        print(
            f"\nAttempt {attempt.attempt}"
        )

        print(attempt.sql)

        if attempt.error:
            print(
                f"Error: {attempt.error}"
            )

    print("\nData:")

    for row in result.data.rows:
        print(row)


if __name__ == "__main__":
    main()