from agent.analytics.chart_generator import (
    ChartGenerator,
)
from agent.llm.deepseek_client import (
    DeepSeekClient,
)
from agent.sql.schemas import QueryResult


def main() -> None:
    generator = ChartGenerator(
        llm=DeepSeekClient(),
    )

    result = QueryResult(
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


    chart = generator.generate(
        question=(
            "查询 CNC-001 最近10条报警详细信息"
            # 查询报警次数最多的设备
            # 查看最近每天生产数量变化趋势
            # 设备状态占比情况
            # 查询 CNC-001 最近10条报警详细信息
        ),
        query_result=result,
    )

    print("=" * 70)
    print("Chart Generator")
    print("=" * 70)

    print(
        chart.model_dump_json(
            indent=2,
        )
    )


if __name__ == "__main__":
    main()