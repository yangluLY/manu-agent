import json

from agent.analytics.chart_prompt import (
    CHART_GENERATION_SYSTEM_PROMPT,
    build_chart_generation_prompt,
)
from agent.analytics.schemas import (
    ChartSeries,
    ChartSpec,
)
from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.schemas import QueryResult


class ChartGenerator:
    """
    BI 图表配置生成器。

    职责：
    - 根据用户问题和 QueryResult 选择图表类型
    - 选择 x / y / category / value 字段
    - 返回结构化 ChartSpec

    不负责：
    - SQL 查询
    - 数据分析
    - 真正绘制图表
    """

    def __init__(
        self,
        llm: DeepSeekClient,
    ):
        self.llm = llm

    def generate(
        self,
        *,
        question: str,
        query_result: QueryResult,
    ) -> ChartSpec:

        if not query_result.rows:
            return ChartSpec(
                type="table",
                title="查询结果",
                data=[],
                reason="查询结果为空，没有可用于生成图表的数据。",
            )

        rows_json = json.dumps(
            query_result.rows,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

        prompt = build_chart_generation_prompt(
            question=question,
            columns=query_result.columns,
            rows_json=rows_json,
        )

        response = self.llm.create_response(
            input_items=prompt,
            instructions=CHART_GENERATION_SYSTEM_PROMPT,
            tools=None,
        )

        content = getattr(
            response,
            "output_text",
            None,
        )

        if not content:
            raise ValueError(
                "Chart generation response "
                "does not contain output_text"
            )

        spec = self._parse_result(content)

        self._validate_fields(
            spec=spec,
            available_columns=set(
                query_result.columns
            ),
        )

        spec.data = query_result.rows

        if spec.type in {"bar", "line"}:
            spec.series = [
                ChartSeries(
                    name=field,
                    field=field,
                )
                for field in spec.y_fields
            ]

        return spec

    def _validate_fields(
        self,
        *,
        spec: ChartSpec,
        available_columns: set[str],
    ) -> None:

        fields: list[str] = []

        if spec.x_field:
            fields.append(spec.x_field)

        fields.extend(spec.y_fields)

        if spec.category_field:
            fields.append(
                spec.category_field
            )

        if spec.value_field:
            fields.append(
                spec.value_field
            )

        invalid_fields = [
            field
            for field in fields
            if field not in available_columns
        ]

        if invalid_fields:
            raise ValueError(
                "ChartSpec contains unknown fields: "
                + ", ".join(invalid_fields)
            )

    def _parse_result(
        self,
        content: str,
    ) -> ChartSpec:

        content = self._clean_json(
            content
        )

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid JSON returned by "
                f"ChartGenerator: {content}"
            ) from exc

        return ChartSpec.model_validate(
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

        if content.endswith("```"):  # noqa: FURB188
            content = content[:-3]

        return content.strip()