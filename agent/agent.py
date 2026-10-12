import json
from collections.abc import Iterator
from time import monotonic
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
        history: list[dict[str, str]] | None = None,
    ) -> str:

        # DeepSeek Responses API 是无状态的。
        # 所以由我们自己维护完整 conversation。
        input_items: list[dict[str, Any]] = [
            {
                "role": item["role"],
                "content": item["content"],
            }
            for item in (history or [])
        ]
        input_items.append(
            {
                "role": "user",
                "content": message,
            }
        )

        # 最多执行 5 轮 Tool，并额外允许模型生成一次最终回答。
        max_tool_rounds = 5

        for round_index in range(max_tool_rounds + 1):

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

            if round_index >= max_tool_rounds:
                raise RuntimeError(
                    "ManuAgent exceeded maximum tool execution rounds."
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

    def chat_stream(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> Iterator[dict[str, str]]:
        """流式执行 Agent，并只向调用方发送最终回答文本。"""
        input_items: list[dict[str, Any]] = [
            {
                "role": item["role"],
                "content": item["content"],
            }
            for item in (history or [])
        ]
        input_items.append(
            {
                "role": "user",
                "content": message,
            }
        )

        max_tool_rounds = 5

        for round_index in range(max_tool_rounds + 1):
            progress_message = (
                "ManuAgent 正在分析问题…"
                if round_index == 0
                else "ManuAgent 正在整理工具结果…"
            )
            yield {
                "type": "status",
                "message": progress_message,
            }
            last_progress_at = monotonic()

            final_response = None
            saw_function_call = False
            emitted_text = False
            reset_sent = False

            with self.llm.create_response_stream(
                input_items=input_items,
                instructions=SYSTEM_PROMPT,
                tools=self.registry.schemas,
            ) as stream:
                for event in stream:
                    event_type = event.type

                    if event_type == "response.output_item.added":
                        item = event.item
                        if item.type == "function_call":
                            saw_function_call = True
                            if emitted_text and not reset_sent:
                                yield {"type": "reset"}
                                reset_sent = True

                    elif event_type == "response.output_text.delta":
                        if not saw_function_call and event.delta:
                            emitted_text = True
                            last_progress_at = monotonic()
                            yield {
                                "type": "delta",
                                "content": event.delta,
                            }

                    elif event_type == "response.reasoning_text.delta":
                        now = monotonic()
                        if now - last_progress_at >= 10:
                            yield {
                                "type": "status",
                                "message": progress_message,
                            }
                            last_progress_at = now

                    elif event_type == "response.completed":
                        final_response = event.response

                    elif event_type == "response.incomplete":
                        reason = getattr(
                            event.response.incomplete_details,
                            "reason",
                            "unknown",
                        )
                        raise RuntimeError(
                            f"DeepSeek response incomplete: {reason}"
                        )

                    elif event_type == "response.failed":
                        error = event.response.error
                        detail = getattr(error, "message", None) or "unknown error"
                        raise RuntimeError(
                            f"DeepSeek response failed: {detail}"
                        )

            if final_response is None:
                raise RuntimeError(
                    "DeepSeek stream ended without a completed response."
                )

            function_calls = [
                item
                for item in final_response.output
                if item.type == "function_call"
            ]

            for item in final_response.output:
                normalized_item = self._normalize_output_item(item)
                if normalized_item is not None:
                    input_items.append(normalized_item)

            if not function_calls:
                answer = final_response.output_text
                if not answer:
                    raise RuntimeError(
                        "DeepSeek returned no final text."
                    )

                if not emitted_text:
                    yield {
                        "type": "delta",
                        "content": answer,
                    }

                yield {
                    "type": "done",
                    "answer": answer,
                }
                return

            if round_index >= max_tool_rounds:
                raise RuntimeError(
                    "ManuAgent exceeded maximum tool execution rounds."
                )

            if emitted_text and not reset_sent:
                yield {"type": "reset"}

            for function_call in function_calls:
                yield {
                    "type": "status",
                    "message": f"正在执行工具：{function_call.name}",
                }

                result = self._execute_function_call(function_call)
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
