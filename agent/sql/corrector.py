import json

from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.prompt import (
    SQL_CORRECTION_SYSTEM_PROMPT,
    build_sql_correction_prompt,
)
from agent.sql.schema_provider import SchemaProvider
from agent.sql.schemas import SQLGenerationResult


class SQLCorrector:
    """
    SQL 自动修正器。

    职责：
    - 接收执行失败的 SQL
    - 接收数据库错误信息
    - 结合数据库 Schema
    - 生成修正后的 SQL

    不负责：
    - SQL 执行
    - SQL 安全校验
    """

    def __init__(
        self,
        llm: DeepSeekClient,
        schema_provider: SchemaProvider,
    ):
        self.llm = llm
        self.schema_provider = schema_provider

    def correct(
        self,
        *,
        question: str,
        failed_sql: str,
        error_message: str,
    ) -> SQLGenerationResult:

        database_schema = (
            self.schema_provider.to_prompt_text()
        )

        prompt = build_sql_correction_prompt(
            question=question,
            database_schema=database_schema,
            failed_sql=failed_sql,
            error_message=error_message,
        )

        response = self.llm.create_response(
            input_items=prompt,
            instructions=SQL_CORRECTION_SYSTEM_PROMPT,
            tools=None,
        )

        content = getattr(
            response,
            "output_text",
            None,
        )

        if not content:
            raise ValueError(
                "LLM correction response "
                "does not contain output_text"
            )

        return self._parse_result(content)

    def _parse_result(
        self,
        content: str,
    ) -> SQLGenerationResult:

        content = self._clean_json(content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid JSON returned by "
                f"SQL corrector: {content}"
            ) from exc

        return SQLGenerationResult.model_validate(
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