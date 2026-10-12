import json

from agent.analytics.prompt import (
    DATA_ANALYSIS_SYSTEM_PROMPT,
    build_data_analysis_prompt,
)
from agent.analytics.schemas import (
    DataAnalysisResult,
)
from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.schemas import QueryResult


class DataAnalyzer:
    """
    MES 查询结果分析器。

    职责：
    - 接收 QueryResult
    - 将结构化数据交给 LLM
    - 输出业务摘要和关键洞察

    不负责：
    - SQL 生成
    - SQL 执行
    - 图表生成
    """

    def __init__(
        self,
        llm: DeepSeekClient,
    ):
        self.llm = llm

    def analyze(
        self,
        *,
        question: str,
        query_result: QueryResult,
    ) -> DataAnalysisResult:

        # 无数据时没必要调用 LLM
        if not query_result.rows:
            return DataAnalysisResult(
                summary="当前查询未返回可分析的数据。",
                key_findings=[],
                recommendations=[],
                limitations=[
                    "查询结果为空，无法进行进一步数据分析。"
                ],
            )

        rows_json = json.dumps(
            query_result.rows,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

        prompt = build_data_analysis_prompt(
            question=question,
            columns=query_result.columns,
            rows_json=rows_json,
            row_count=query_result.row_count,
            truncated=query_result.truncated,
        )

        response = self.llm.create_response(
            input_items=prompt,
            instructions=DATA_ANALYSIS_SYSTEM_PROMPT,
            tools=None,
        )

        content = getattr(
            response,
            "output_text",
            None,
        )

        if not content:
            raise ValueError(
                "Data analysis response "
                "does not contain output_text"
            )

        result = self._parse_result(content)

        # Executor 已经告诉我们数据被截断，
        # 不完全依赖 LLM 自己记得说明。
        if query_result.truncated:
            limitation = (
                "查询结果已被截断，当前分析仅基于返回的部分数据。"
            )

            if limitation not in result.limitations:
                result.limitations.append(
                    limitation
                )

        return result

    def _parse_result(
        self,
        content: str,
    ) -> DataAnalysisResult:

        content = self._clean_json(
            content
        )

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid JSON returned by "
                f"DataAnalyzer: {content}"
            ) from exc

        return DataAnalysisResult.model_validate(
            data
        )

    @staticmethod
    def _clean_json(
        content: str,
    ) -> str:

        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]

        elif content.startswith("```"):
            content = content[3:]

        content = content.removesuffix("```")

        return content.strip()