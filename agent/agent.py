import json
from typing import Any

from agent.executor import ToolExecutor
from agent.llm.deepseek_client import DeepSeekClient
from agent.prompts.system_prompt import SYSTEM_PROMPT
from agent.registry import ToolRegistry
from agent.tools.types import ToolResult


class ManuAgent:
    """
    ManuAgent 主循环。

    职责：
    1. 将用户问题发送给 LLM
    2. 判断 LLM 是否请求调用 Tool
    3. 调用 ToolExecutor 执行 Tool
    4. 将 ToolResult 回传给 LLM
    5. 循环直到获得最终自然语言回答
    """

    def __init__(
        self,
        registry: ToolRegistry,
        llm: DeepSeekClient,
    ):
        self.registry = registry
        self.llm = llm

        self.executor = ToolExecutor(
            registry=registry,
        )

    def chat(
        self,
        message: str,
    ) -> str:

        # DeepSeek Responses API 是无状态的。
        # 所以由我们自己维护完整 conversation。
        input_items: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": message,
            }
        ]

        # 防止模型不断调用 Tool，造成死循环
        max_tool_rounds = 5

        for _ in range(max_tool_rounds):

            response = self.llm.create_response(
                input_items=input_items,
                instructions=SYSTEM_PROMPT,
                tools=self.registry.schemas,
            )

            # -------------------------------------------------
            # 1. 找出这一轮所有 Function Call
            # -------------------------------------------------

            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            # -------------------------------------------------
            # 2. 把模型本轮输出加入 conversation
            #
            # 包括：
            # - reasoning
            # - message
            # - function_call
            #
            # DeepSeek Responses API 无状态，
            # 下一轮必须重新传完整历史。
            # -------------------------------------------------

            for item in response.output:
                normalized_item = self._normalize_output_item(
                    item
                )

                if normalized_item is not None:
                    input_items.append(
                        normalized_item
                    )

            # -------------------------------------------------
            # 3. 如果没有 Function Call，
            #    说明模型已经生成最终回答
            # -------------------------------------------------

            if not function_calls:

                if response.output_text:
                    return response.output_text

                raise RuntimeError(
                    "DeepSeek returned no final text."
                )

            # -------------------------------------------------
            # 4. 执行所有 Tool Call
            # -------------------------------------------------

            for function_call in function_calls:

                result = self._execute_function_call(
                    function_call
                )

                # -------------------------------------------------
                # 5. 把 ToolResult 作为 function_call_output
                #    放回 conversation
                # -------------------------------------------------

                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": function_call.call_id,
                        "output": json.dumps(
                            result.to_dict(),
                            ensure_ascii=False,
                        ),
                    }
                )

            # 当前轮结束后进入下一次循环：
            #
            # 完整 conversation
            #       ↓
            # DeepSeek
            #       ↓
            # 根据 ToolResult 继续推理
            #       ↓
            # 可能继续调用 Tool
            # 或生成最终回答

        raise RuntimeError(
            "ManuAgent exceeded maximum tool execution rounds."
        )

    def _execute_function_call(
        self,
        function_call,
    ) -> ToolResult:
        """
        将 DeepSeek 返回的 function_call
        转换成真正的 Tool 执行。
        """

        try:
            arguments = json.loads(
                function_call.arguments
            )

        except json.JSONDecodeError:

            return ToolResult.fail(
                code="INVALID_TOOL_ARGUMENTS",
                message="Tool arguments are not valid JSON",
                details={
                    "tool_name": function_call.name,
                },
            )

        # JSON 本身必须是 object
        if not isinstance(arguments, dict):

            return ToolResult.fail(
                code="INVALID_TOOL_ARGUMENTS",
                message="Tool arguments must be a JSON object",
                details={
                    "tool_name": function_call.name,
                },
            )

        return self.executor.execute(
            tool_name=function_call.name,
            arguments=arguments,
        )

    @staticmethod
    def _normalize_output_item(
        item,
    ) -> dict[str, Any] | None:
        """
        把 DeepSeek response.output 中的对象，
        转换成下一次 Responses API 可以接受的 input item。

        当前处理：
        - reasoning
        - function_call
        - assistant message
        """

        # -------------------------------
        # reasoning
        # -------------------------------

        if item.type == "reasoning":

            content = []

            for part in item.content or []:

                if part.type == "reasoning_text":
                    content.append(
                        {
                            "type": "reasoning_text",
                            "text": part.text,
                        }
                    )

            if not content:
                return None

            return {
                "type": "reasoning",
                "content": content,
            }

        # -------------------------------
        # function_call
        # -------------------------------

        if item.type == "function_call":

            return {
                "type": "function_call",
                "call_id": item.call_id,
                "name": item.name,
                "arguments": item.arguments,
            }

        # -------------------------------
        # assistant message
        # -------------------------------

        if item.type == "message":

            content = []

            for part in item.content or []:

                if part.type == "output_text":
                    content.append(
                        {
                            "type": "output_text",
                            "text": part.text,
                        }
                    )

            if not content:
                return None

            return {
                "role": "assistant",
                "content": content,
            }

        return None