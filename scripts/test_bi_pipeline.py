from agent.analytics.analyzer import (
    DataAnalyzer,
)
from agent.analytics.chart_generator import (
    ChartGenerator,
)
from agent.analytics.pipeline import (
    BIPipeline,
    convert_natural_language_to_bi,
)
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

    generator = SQLGenerator(
        llm=llm,
        schema_provider=schema_provider,
    )

    validator = SQLValidator()

    executor = SQLExecutor(
        engine=engine,
        validator=validator,
    )

    corrector = SQLCorrector(
        llm=llm,
        schema_provider=schema_provider,
    )

    sql_pipeline = SQLPipeline(
        generator=generator,
        corrector=corrector,
        executor=executor,
        max_retries=2,
    )

    analyzer = DataAnalyzer(
        llm=llm,
    )

    chart_generator = ChartGenerator(
        llm=llm,
    )

    question = (
        "查询报警次数最多的5台设备"
    )

    pipeline = BIPipeline(
        sql_pipeline=sql_pipeline,
        analyzer=analyzer,
        chart_generator=chart_generator,
    )

    result = convert_natural_language_to_bi(
        question,
        pipeline=pipeline,
    )

    print("=" * 70)
    print("Question")
    print("=" * 70)

    print(question)

    print("\nSQL:")
    print(result.sql)

    print("\nData:")

    for row in result.data.rows:
        print(row)

    print("\nAnalysis:")
    print(result.analysis.summary)

    print("\nChart:")
    print(
        result.chart.model_dump_json(
            indent=2,
        )
    )

    print("\nECharts Option:")
    print(result.echarts_option)


if __name__ == "__main__":
    main()
