from agent.analytics.analyzer import DataAnalyzer
from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.corrector import SQLCorrector
from agent.sql.executor import SQLExecutor
from agent.sql.generator import SQLGenerator
from agent.sql.pipeline import SQLPipeline
from agent.sql.schema_provider import SchemaProvider
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

    question = (
        "查询最近生产记录中实际产量最高的工单"
    )
    # 查询报警次数最多的5台设备
    # 统计每台设备最近7天的生产数量
    # 查询库存最低的5种物料
    # 统计不同状态的工单数量
    # 查询最近生产记录中实际产量最高的工单


    # =================================
    # 1. Natural Language -> Data
    # =================================

    sql_result = sql_pipeline.run(
        question
    )

    print("=" * 70)
    print("SQL")
    print("=" * 70)

    print(sql_result.sql)

    print("\nData:")

    for row in sql_result.data.rows:
        print(row)

    # =================================
    # 2. Data -> Insight
    # =================================

    analysis = analyzer.analyze(
        question=question,
        query_result=sql_result.data,
    )

    print("\n")
    print("=" * 70)
    print("Analysis")
    print("=" * 70)

    print("\nSummary:")
    print(analysis.summary)

    print("\nKey Findings:")

    for finding in analysis.key_findings:
        print(f"- {finding}")

    print("\nRecommendations:")

    for recommendation in analysis.recommendations:
        print(f"- {recommendation}")


if __name__ == "__main__":
    main()