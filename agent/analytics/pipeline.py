from agent.analytics.analyzer import DataAnalyzer
from agent.analytics.chart_generator import ChartGenerator
from agent.analytics.echarts import chart_spec_to_echarts
from agent.analytics.schemas import BIPipelineResult
from agent.sql.pipeline import SQLPipeline


class BIPipeline:
    """串联 V3.1 到 V3.7 的只读 BI 查询管线。

    执行顺序：

    1. SQLGenerator 内部通过 SchemaProvider 发现数据库 Schema；
    2. SQLGenerator 完成 Text-to-SQL；
    3. SQLExecutor 在执行前调用 SQLValidator 做安全校验；
    4. SQLExecutor 执行只读 SQL；
    5. SQLPipeline 在执行错误时调用 SQLCorrector 并重试；
    6. DataAnalyzer 分析真实查询结果；
    7. ChartGenerator 生成 ChartSpec，再转换为 ECharts option。
    """

    def __init__(
        self,
        *,
        sql_pipeline: SQLPipeline,
        analyzer: DataAnalyzer,
        chart_generator: ChartGenerator,
    ):
        self.sql_pipeline = sql_pipeline
        self.analyzer = analyzer
        self.chart_generator = chart_generator

    def run(
        self,
        question: str,
    ) -> BIPipelineResult:
        normalized_question = question.strip()

        if not normalized_question:
            raise ValueError("BI question cannot be empty")

        sql_result = self.sql_pipeline.run(
            normalized_question
        )

        analysis = self.analyzer.analyze(
            question=normalized_question,
            query_result=sql_result.data,
        )

        chart = self.chart_generator.generate(
            question=normalized_question,
            query_result=sql_result.data,
        )

        return BIPipelineResult(
            question=normalized_question,
            sql=sql_result.sql,
            data=sql_result.data,
            analysis=analysis,
            chart=chart,
            echarts_option=chart_spec_to_echarts(chart),
            attempts=sql_result.attempts,
            retry_count=sql_result.retry_count,
        )


def convert_natural_language_to_bi(
    question: str,
    *,
    pipeline: BIPipeline,
) -> BIPipelineResult:
    """统一转换函数：输入自然语言，返回数据、分析和 ECharts 配置。"""

    return pipeline.run(question)
