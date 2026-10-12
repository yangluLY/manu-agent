from types import SimpleNamespace

from agent.agent import ManuAgent
from agent.registry import ToolRegistry
from agent.tools.types import ToolResult


class StubStream:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return iter(self.events)

    def __exit__(self, _exc_type, _exc, _traceback):
        return None


class StubStreamingDeepSeekClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def create_response_stream(self, **request):
        self.requests.append(request)
        return StubStream(self.responses.pop(0))


def completed_event(*, output, output_text):
    return SimpleNamespace(
        type="response.completed",
        response=SimpleNamespace(
            output=output,
            output_text=output_text,
        ),
    )


def test_chat_stream_emits_text_deltas_and_done_with_history():
    llm = StubStreamingDeepSeekClient(
        [
            [
                SimpleNamespace(
                    type="response.output_item.added",
                    item=SimpleNamespace(type="message"),
                ),
                SimpleNamespace(
                    type="response.output_text.delta",
                    delta="设备正在",
                ),
                SimpleNamespace(
                    type="response.output_text.delta",
                    delta="运行。",
                ),
                completed_event(output=[], output_text="设备正在运行。"),
            ]
        ]
    )
    agent = ManuAgent(registry=ToolRegistry(), llm=llm)
    history = [
        {"role": "user", "content": "查询 MC-003"},
        {"role": "assistant", "content": "已找到设备。"},
    ]

    events = list(
        agent.chat_stream(
            "它的状态是什么？",
            history=history,
        )
    )

    assert events == [
        {"type": "status", "message": "ManuAgent 正在分析问题…"},
        {"type": "delta", "content": "设备正在"},
        {"type": "delta", "content": "运行。"},
        {"type": "done", "answer": "设备正在运行。"},
    ]
    assert llm.requests[0]["input_items"] == [
        *history,
        {"role": "user", "content": "它的状态是什么？"},
    ]


def test_chat_stream_resets_draft_then_executes_tool_and_streams_answer():
    function_call = SimpleNamespace(
        type="function_call",
        call_id="call-1",
        name="lookup_machine",
        arguments='{"machine_code":"MC-003"}',
    )
    llm = StubStreamingDeepSeekClient(
        [
            [
                SimpleNamespace(
                    type="response.output_item.added",
                    item=SimpleNamespace(type="message"),
                ),
                SimpleNamespace(
                    type="response.output_text.delta",
                    delta="我先看看。",
                ),
                SimpleNamespace(
                    type="response.output_item.added",
                    item=function_call,
                ),
                completed_event(output=[function_call], output_text="我先看看。"),
            ],
            [
                SimpleNamespace(
                    type="response.output_text.delta",
                    delta="MC-003 正常运行。",
                ),
                completed_event(output=[], output_text="MC-003 正常运行。"),
            ],
        ]
    )
    registry = ToolRegistry()
    registry.register(
        name="lookup_machine",
        handler=lambda machine_code: ToolResult.ok(
            {"machine_code": machine_code, "status": "running"}
        ),
        schema={
            "type": "function",
            "name": "lookup_machine",
            "parameters": {
                "type": "object",
                "properties": {"machine_code": {"type": "string"}},
                "required": ["machine_code"],
            },
        },
    )
    agent = ManuAgent(registry=registry, llm=llm)

    events = list(agent.chat_stream("查询 MC-003"))

    assert {"type": "reset"} in events
    assert {
        "type": "status",
        "message": "正在执行工具：lookup_machine",
    } in events
    assert events[-2:] == [
        {"type": "delta", "content": "MC-003 正常运行。"},
        {"type": "done", "answer": "MC-003 正常运行。"},
    ]
    second_input = llm.requests[1]["input_items"]
    assert second_input[-2]["type"] == "function_call"
    assert second_input[-1]["type"] == "function_call_output"
    assert '"status": "running"' in second_input[-1]["output"]
