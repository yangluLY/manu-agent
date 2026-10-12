import json

from agent.llm.deepseek_client import DeepSeekClient
from agent.sql.prompt import (
    SQL_GENERATION_SYSTEM_PROMPT,
    build_sql_generation_prompt,
)
from agent.sql.schema_provider import SchemaProvider
from agent.sql.schemas import SQLGenerationResult


class SQLGenerator:
    """
    Text-to-SQL 生成器。

    职责：
    - 获取数据库 Schema
    - 构建 Text-to-SQL Prompt
    - 调用 LLM
    - 将 LLM 输出解析成 SQLGenerationResult

    不负责：
    - SQL 安全校验
    - SQL 执行
    - 数据分析
    """

    def __init__(
        self,
        llm: DeepSeekClient,
        schema_provider: SchemaProvider,
    ):
        self.llm = llm
        self.schema_provider = schema_provider

    def generate(
        self,
        question: str,
    ) -> SQLGenerationResult:
        """
        根据自然语言问题生成 SQL。
        """

        database_schema = self.schema_provider.to_prompt_text()

        user_prompt = build_sql_generation_prompt(
            question=question,
            database_schema=database_schema,
        )

        content = self._call_llm(user_prompt)

        return self._parse_result(content)

    def _call_llm(
        self,
        user_prompt: str,
    ) -> str:
        """
        调用项目现有的 DeepSeekClient。
        """

        response = self.llm.create_response(
            input_items=user_prompt,
            instructions=SQL_GENERATION_SYSTEM_PROMPT,
            tools=None,
        )

        output_text = getattr(response, "output_text", None)

        if not output_text:
            raise ValueError(
                "LLM response does not contain output_text"
            )

        return output_text

    def _parse_result(
        self,
        content: str,
    ) -> SQLGenerationResult:
        """
        将模型 JSON 输出解析成结构化结果。
        """

        content = self._clean_json(content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON returned by LLM: {content}"
            ) from exc

        return SQLGenerationResult.model_validate(data)

    @staticmethod
    def _clean_json(content: str) -> str:
        """
        兼容模型偶尔返回 Markdown JSON code block。
        """

        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]

        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):  # noqa: FURB188
            content = content[:-3]

        return content.strip()