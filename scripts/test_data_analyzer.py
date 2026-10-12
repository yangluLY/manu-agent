from agent.analytics.analyzer import DataAnalyzer
from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.schemas import QueryResult


def main() -> None:
    analyzer = DataAnalyzer(
        llm=DeepSeekClient(),
    )

    query_result = QueryResult(
        columns=[
            "machine_code",
            "alarm_count",
        ],
        rows=[
            {
                "machine_code": "CNC-001",
                "alarm_count": 35,
            },
            {
                "machine_code": "CNC-002",
                "alarm_count": 12,
            },
            {
                "machine_code": "CNC-003",
                "alarm_count": 8,
            },
        ],
        row_count=3,
        execution_time_ms=5.2,
        truncated=False,
    )

    result = analyzer.analyze(
        question="哪些设备报警最频繁？",
        query_result=query_result,
    )

    print("=" * 70)
    print("Data Analysis")
    print("=" * 70)

    print("\nSummary:")
    print(result.summary)

    print("\nKey Findings:")

    for finding in result.key_findings:
        print(f"- {finding}")

    print("\nRecommendations:")

    for recommendation in result.recommendations:
        print(f"- {recommendation}")

    print("\nLimitations:")

    for limitation in result.limitations:
        print(f"- {limitation}")


if __name__ == "__main__":
    main()