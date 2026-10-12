from types import SimpleNamespace

from agent.agent import ManuAgent
from agent.registry import ToolRegistry


class StubDeepSeekClient:
    def __init__(self):
        self.requests = []

    def create_response(self, **request):
        self.requests.append(request)
        return SimpleNamespace(
            output=[],
            output_text="设备 MC-003 当前没有活动报警。",
        )


def test_agent_sends_history_before_current_message():
    llm = StubDeepSeekClient()
    agent = ManuAgent(
        registry=ToolRegistry(),
        llm=llm,
    )
    history = [
        {"role": "user", "content": "查询设备 MC-003"},
        {"role": "assistant", "content": "设备 MC-003 正在运行。"},
    ]

    answer = agent.chat(
        "它现在还有报警吗？",
        history=history,
    )

    assert answer == "设备 MC-003 当前没有活动报警。"
    assert llm.requests[0]["input_items"] == [
        *history,
        {"role": "user", "content": "它现在还有报警吗？"},
    ]
