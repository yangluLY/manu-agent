
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.dependencies.auth import (
    CurrentUser,
    get_current_user,
)
from apps.api.app.dependencies.workflow import (
    get_workflow_runtime,
)
from apps.api.app.dependencies.workflow_store import (
    get_thread_store,
)
from apps.api.app.routers.workflow import (
    router as workflow_router,
)

TEST_USER = CurrentUser(
    user_id="test-sse-user",
    roles=frozenset({"viewer"}),
)


class FakeThreadStore:
    def __init__(self):
        self.records = {}

    def register(
        self,
        thread_id: str,
        owner_id: str,
    ):
        self.records[thread_id] = owner_id



class MockWorkflow:
    """
    模拟 LangGraph updates 事件。
    """

    def stream(
        self,
        initial_state,
        config,
        stream_mode,
    ):
        assert stream_mode == "updates"
        assert config["configurable"]["thread_id"]

        yield {
            "initialize": {
                "workflow_id": "test-workflow-001",
                "workflow_status": "running",
                "execution_events": [],
            }
        }

        yield {
            "router": {
                "route": "mes",
                "route_reason": "设备状态查询",
            }
        }

        yield {
            "simple_planner": {
                "plan": [
                    {
                        "id": 1,
                        "agent": "mes",
                        "task": initial_state["user_input"],
                    }
                ],
                "current_step": 0,
            }
        }

        yield {
            "step_executor": {
                "current_step": 1,
                "step_results": [
                    {
                        "step_id": 1,
                        "agent": "mes",
                        "task": initial_state["user_input"],
                        "status": "success",
                        "output": "CNC-001 运行正常",
                        "duration_ms": 12.5,
                        "attempts": 1,
                        "data": None,
                        "sources": [],
                        "sql": None,
                        "chart": None,
                    }
                ],
                "result": "CNC-001 运行正常",
            }
        }

        yield {
            "response": {
                "workflow_status": "completed",
                "final_answer": "CNC-001 运行正常",
            }
        }


def create_client(workflow=None):
    if workflow is None:
        workflow = MockWorkflow()

    app = FastAPI()

    app.include_router(
        workflow_router,
        prefix="/api/v1",
    )

    fake_thread_store = FakeThreadStore()

    app.dependency_overrides[
        get_current_user
    ] = lambda: TEST_USER

    app.dependency_overrides[
        get_workflow_runtime
    ] = lambda: workflow

    app.dependency_overrides[
        get_thread_store
    ] = lambda: fake_thread_store

    return TestClient(app)



def parse_sse(text):
    """
    将测试响应解析为：
    [
        {"event": "...", "data": {...}},
        ...
    ]
    """

    events = []

    for block in text.strip().split("\n\n"):
        event_name = None
        data_text = None

        for line in block.splitlines():
            if line.startswith("event: "):
                event_name = line[7:]

            elif line.startswith("data: "):
                data_text = line[6:]

        if event_name and data_text:
            events.append({
                "event": event_name,
                "data": json.loads(data_text),
            })

    return events


def test_stream_content_type():
    client = create_client()

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={
            "message": "查询 CNC-001"
        },
    )

    assert response.status_code == 200

    assert "text/event-stream" in (
        response.headers["content-type"]
    )

    assert response.headers["x-thread-id"]


def test_stream_event_order():
    client = create_client()

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={"message": "查询 CNC-001"},
    )

    events = parse_sse(response.text)

    names = [
        item["event"]
        for item in events
    ]

    assert names == [
        "workflow_started",
        "route_completed",
        "plan_created",
        "step_completed",
        "workflow_completed",
    ]


def test_route_and_plan_events():
    client = create_client()

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={"message": "查询 CNC-001"},
    )

    events = parse_sse(response.text)

    route_event = next(
        item
        for item in events
        if item["event"] == "route_completed"
    )

    assert route_event["data"]["route"] == "mes"

    plan_event = next(
        item
        for item in events
        if item["event"] == "plan_created"
    )

    assert plan_event["data"]["total_steps"] == 1
    assert plan_event["data"]["steps"][0]["agent"] == "mes"


def test_step_completed_event():
    client = create_client()

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={"message": "查询 CNC-001"},
    )

    events = parse_sse(response.text)

    step_event = next(
        item
        for item in events
        if item["event"] == "step_completed"
    )

    assert step_event["data"]["step_id"] == 1
    assert step_event["data"]["agent"] == "mes"
    assert step_event["data"]["status"] == "success"
    assert step_event["data"]["attempts"] == 1


def test_workflow_completed_event():
    client = create_client()

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={"message": "查询 CNC-001"},
    )

    events = parse_sse(response.text)

    final_event = events[-1]

    assert final_event["event"] == "workflow_completed"

    data = final_event["data"]

    assert data["thread_id"]
    assert data["workflow_id"] == "test-workflow-001"
    assert data["status"] == "completed"
    assert data["answer"] == "CNC-001 运行正常"
    assert len(data["steps"]) == 1


def test_stream_invalid_message():
    client = create_client()

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={"message": "  "},
    )

    assert response.status_code == 422


def test_stream_internal_error():
    class FailingWorkflow:
        def stream(
            self,
            initial_state,
            config,
            stream_mode,
        ):
            yield {
                "initialize": {
                    "workflow_id": "test-error",
                }
            }

            raise RuntimeError(
                "数据库密码为 secret-password"
            )

    client = create_client(
        FailingWorkflow()
    )

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={"message": "查询 CNC-001"},
    )

    events = parse_sse(response.text)

    assert events[-1]["event"] == "workflow_failed"

    assert events[-1]["data"]["code"] == (
        "WORKFLOW_EXECUTION_ERROR"
    )

    assert "secret-password" not in response.text
