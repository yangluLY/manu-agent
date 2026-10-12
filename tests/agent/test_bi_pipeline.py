from datetime import date
from decimal import Decimal

from agent.analytics.echarts import chart_spec_to_echarts
from agent.analytics.pipeline import (
    BIPipeline,
    convert_natural_language_to_bi,
)
from agent.analytics.schemas import (
    ChartSeries,
    ChartSpec,
    DataAnalysisResult,
)
from agent.sql.schemas import (
    QueryResult,
    SQLAttempt,
    SQLPipelineResult,
)


def test_bi_pipeline_connects_sql_analysis_and_echarts():
    calls: list[str] = []
    query_result = QueryResult(
        columns=["machine_code", "alarm_count"],
        rows=[
            {"machine_code": "MC-003", "alarm_count": 12},
            {"machine_code": "MC-001", "alarm_count": 7},
        ],
        row_count=2,
        execution_time_ms=4.2,
    )

    class StubSQLPipeline:
        def run(self, question):
            calls.append(f"sql:{question}")
            return SQLPipelineResult(
                question=question,
                sql=(
                    "SELECT m.code AS machine_code, COUNT(*) AS alarm_count "
                    "FROM machines m JOIN machine_alarms a ON a.machine_id = m.id "
                    "GROUP BY m.code ORDER BY alarm_count DESC LIMIT 5"
                ),
                data=query_result,
                attempts=[
                    SQLAttempt(
                        attempt=1,
                        sql="SELECT ...",
                    )
                ],
            )

    class StubAnalyzer:
        def analyze(self, *, question, query_result):
            assert query_result is not None
            calls.append(f"analysis:{question}")
            return DataAnalysisResult(
                summary="MC-003 报警次数最多。",
                key_findings=["MC-003 共 12 次报警"],
            )

    class StubChartGenerator:
        def generate(self, *, question, query_result):
            calls.append(f"chart:{question}")
            return ChartSpec(
                type="bar",
                title="报警次数最多的设备",
                x_field="machine_code",
                y_fields=["alarm_count"],
                series=[
                    ChartSeries(
                        name="alarm_count",
                        field="alarm_count",
                    )
                ],
                data=query_result.rows,
            )

    pipeline = BIPipeline(
        sql_pipeline=StubSQLPipeline(),
        analyzer=StubAnalyzer(),
        chart_generator=StubChartGenerator(),
    )

    result = convert_natural_language_to_bi(
        "  查询报警次数最多的5台设备  ",
        pipeline=pipeline,
    )

    assert calls == [
        "sql:查询报警次数最多的5台设备",
        "analysis:查询报警次数最多的5台设备",
        "chart:查询报警次数最多的5台设备",
    ]
    assert result.question == "查询报警次数最多的5台设备"
    assert result.analysis.summary == "MC-003 报警次数最多。"
    assert result.echarts_option is not None
    assert result.echarts_option["dataset"]["source"] == query_result.rows
    assert result.echarts_option["series"][0]["encode"] == {
        "x": "machine_code",
        "y": "alarm_count",
    }


def test_echarts_conversion_normalizes_database_values():
    option = chart_spec_to_echarts(
        ChartSpec(
            type="line",
            title="每日产量",
            x_field="production_date",
            y_fields=["actual_qty"],
            series=[
                ChartSeries(
                    name="实际产量",
                    field="actual_qty",
                )
            ],
            data=[
                {
                    "production_date": date(2026, 10, 12),
                    "actual_qty": Decimal("12.5"),
                }
            ],
        )
    )

    assert option is not None
    assert option["dataset"]["source"] == [
        {
            "production_date": "2026-10-12",
            "actual_qty": 12.5,
        }
    ]
    assert option["series"][0]["smooth"] is True


def test_table_chart_uses_frontend_table_fallback():
    option = chart_spec_to_echarts(
        ChartSpec(
            type="table",
            title="报警明细",
            data=[{"alarm_code": "E101"}],
        )
    )

    assert option is None
