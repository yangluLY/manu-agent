import os
from typing import Any

from openai import OpenAI


class DeepSeekClient:
    """
    DeepSeek Responses API 客户端。

    职责：
    - 管理 DeepSeek API 配置
    - 调用 Responses API
    - 不负责 Tool 执行
    - 不负责 Agent 循环
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = (
            api_key
            or os.environ.get("DEEPSEEK_API_KEY")
        )

        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY is not configured"
            )

        self.model = (
            model
            or os.environ.get(
                "DEEPSEEK_MODEL",
                "deepseek-flash",
            )
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com",
        )

    def create_response(
        self,
        *,
        input_items: str | list[dict[str, Any]],
        instructions: str,
        tools: list[dict[str, Any]] | None = None,
    ):
        """
        调用 DeepSeek Responses API。

        input_items:
            用户消息以及 Agent 历史中的
            message / reasoning / function_call /
            function_call_output 等 item。

        instructions:
            ManuAgent system prompt。

        tools:
            ToolRegistry 提供的 Responses API Tool Schema。
        """

        request: dict[str, Any] = {
            "model": self.model,
            "instructions": instructions,
            "input": input_items,

            # Responses API 下的 Thinking Mode
            "reasoning": {
                "effort": "low",
            },
        }

        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        return self.client.responses.create(
            **request
        )