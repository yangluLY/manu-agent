
import json
from uuid import uuid4

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
from apps.api.app.routers.workflow import router

TEST_USER = CurrentUser(
    user_id="test-operator",
    roles=frozenset({"viewer"}),
)


class FakeThreadStore:
    def __init__(self):
        self.records = {}

    def register(self, thread_id, owner_id):
        if thread_id in self.records:
            if self.records[thread_id] != owner_id:
                raise ValueError("线程归属冲突")
        else:
            self.records[thread_id] = owner_id


class FakeWorkflow:
    @staticmethod
    def make_state(message):
        return {
            "workflow_id": str(uuid4()),
            "workflow_status": "completed",
            "route": "mes",
            "route_reason": "设备查询",
            "final_answer": "CNC-001 设备运行正常",
            "step_results": [
                {
                    "step_id": 1,
                    "agent": "mes",
                    "task": message,
                    "status": "success",
                    "output": "CNC-001 设备运行正常",
                    "duration_ms": 10,
                    "attempts": 1,
                    "sources": [],
                    "data": None,
                    "sql": None,
                    "chart": None,
                }
            ],
            "execution_events": [],
        }

    def invoke(self, state, config):
        return self.make_state(
            state["user_input"]
        )

    def stream(self, state, config, stream_mode):
        assert stream_mode == "updates"

        final_state = self.make_state(
            state["user_input"]
        )

        yield {
            "initialize": {
                "workflow_id": final_state["workflow_id"],
                "workflow_status": "running",
            }
        }

        yield {
            "router": {
                "route": "mes",
                "route_reason": "设备查询",
            }
        }

        yield {
            "simple_planner": {
                "plan": [
                    {
                        "id": 1,
                        "agent": "mes",
                        "task": state["user_input"],
                    }
                ]
            }
        }

        yield {
            "step_executor": {
                "step_results": final_state["step_results"]
            }
        }

        yield {
            "response": {
                "workflow_status": "completed",
                "final_answer": final_state["final_answer"],
            }
        }


def create_client(authenticated=True):
    app = FastAPI()

    app.include_router(
        router,
        prefix="/api/v1",
    )

    store = FakeThreadStore()

    app.dependency_overrides[
        get_thread_store
    ] = lambda: store

    app.dependency_overrides[
        get_workflow_runtime
    ] = lambda: FakeWorkflow()

    if authenticated:
        app.dependency_overrides[
            get_current_user
        ] = lambda: TEST_USER

    return TestClient(app), store


def test_unauthenticated_chat():
    client, store = create_client(
        authenticated=False
    )

    response = client.post(
        "/api/v1/workflow/chat",
        json={"message": "查询 CNC-001"},
    )

    assert response.status_code == 401
    assert store.records == {}


def test_unauthenticated_stream():
    client, store = create_client(
        authenticated=False
    )

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={"message": "查询 CNC-001"},
    )

    assert response.status_code == 401
    assert store.records == {}


def test_authenticated_chat_registers_owner():
    client, store = create_client()

    response = client.post(
        "/api/v1/workflow/chat",
        json={"message": "查询 CNC-001"},
    )

    assert response.status_code == 200

    data = response.json()
    thread_id = data["thread_id"]

    assert store.records[thread_id] == (
        TEST_USER.user_id
    )

    assert data["status"] == "completed"
    assert data["route"] == "mes"


def test_authenticated_stream_registers_owner():
    client, store = create_client()

    response = client.post(
        "/api/v1/workflow/chat/stream",
        json={"message": "查询 CNC-001"},
    )

    assert response.status_code == 200

    thread_id = response.headers["x-thread-id"]

    assert store.records[thread_id] == (
        TEST_USER.user_id
    )

    assert "event: workflow_started" in response.text
    assert "event: route_completed" in response.text
    assert "event: step_completed" in response.text
    assert "event: workflow_completed" in response.text


def test_invalid_message_does_not_create_thread():
    client, store = create_client()

    response = client.post(
        "/api/v1/workflow/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422
    assert store.records == {}


def test_workflow_does_not_expose_secret():
    class BrokenWorkflow:
        def invoke(self, state, config):
            raise RuntimeError(
                "DATABASE_PASSWORD=secret-value"
            )

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    app.dependency_overrides[
        get_current_user
    ] = lambda: TEST_USER

    app.dependency_overrides[
        get_thread_store
    ] = lambda: FakeThreadStore()

    app.dependency_overrides[
        get_workflow_runtime
    ] = lambda: BrokenWorkflow()

    client = TestClient(app)

    response = client.post(
        "/api/v1/workflow/chat",
        json={"message": "查询设备状态"},
    )

    assert response.status_code == 500
    assert "secret-value" not in response.text
