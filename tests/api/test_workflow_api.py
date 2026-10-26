
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
    user_id="test-workflow-user",
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
        existing = self.records.get(thread_id)

        if existing is not None and existing != owner_id:
            raise ValueError("线程归属冲突")

        self.records[thread_id] = owner_id

    def assert_owner(
        self,
        thread_id: str,
        user_id: str,
    ):
        if self.records.get(thread_id) != user_id:
            raise PermissionError("工作流不存在或无访问权限")

class MockWorkflow:
    def invoke(self, state, config):
        return {
            "workflow_id": str(uuid4()),
            "workflow_status": "completed",
            "route": "mes",
            "route_reason": "设备查询",
            "final_answer": "CNC-001 当前运行正常",
            "step_results": [
                {
                    "step_id": 1,
                    "agent": "mes",
                    "task": state["user_input"],
                    "status": "success",
                    "output": "CNC-001 当前运行正常",
                    "duration_ms": 5.0,
                    "data": None,
                    "sources": [],
                    "sql": None,
                    "chart": None,
                }
            ],
            "execution_events": [],
        }


def create_test_client(
    workflow=None,
):
    app = FastAPI()

    app.include_router(
        router,
        prefix="/api/v1",
    )

    mock = workflow or MockWorkflow()

    app.dependency_overrides[
        get_workflow_runtime
    ] = lambda: mock
    app.dependency_overrides[
        get_current_user
    ] = lambda: TEST_USER

    app.dependency_overrides[
        get_thread_store
    ] = lambda: FakeThreadStore()

    return TestClient(app)


def test_workflow_health():
    client = create_test_client()

    response = client.get(
        "/api/v1/workflow/health"
    )

    assert response.status_code == 200

    assert response.json()["status"] == "ok"


def test_workflow_chat_success():
    client = create_test_client()

    response = client.post(
        "/api/v1/workflow/chat",
        json={
            "message": "查询 CNC-001 设备状态"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["thread_id"]
    assert data["workflow_id"]
    assert data["status"] == "completed"
    assert data["route"] == "mes"

    assert data["answer"] == (
        "CNC-001 当前运行正常"
    )

    assert len(data["steps"]) == 1

    assert data["steps"][0]["agent"] == "mes"
    assert data["steps"][0]["status"] == "success"


def test_workflow_empty_message():
    client = create_test_client()

    response = client.post(
        "/api/v1/workflow/chat",
        json={"message": ""},
    )

    assert response.status_code == 422


def test_workflow_whitespace_message():
    client = create_test_client()

    response = client.post(
        "/api/v1/workflow/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_workflow_missing_message():
    client = create_test_client()

    response = client.post(
        "/api/v1/workflow/chat",
        json={},
    )

    assert response.status_code == 422


def test_workflow_unique_thread_ids():
    client = create_test_client()

    first = client.post(
        "/api/v1/workflow/chat",
        json={"message": "查询设备状态"},
    )

    second = client.post(
        "/api/v1/workflow/chat",
        json={"message": "查询设备报警"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert (
        first.json()["thread_id"]
        != second.json()["thread_id"]
    )


def test_workflow_internal_error():
    class FailingWorkflow:
        def invoke(self, state, config):
            raise RuntimeError(
                "模拟内部数据库连接异常"
            )

    client = create_test_client(
        FailingWorkflow()
    )

    response = client.post(
        "/api/v1/workflow/chat",
        json={"message": "查询设备状态"},
    )

    assert response.status_code == 500

    # 不应将内部异常信息返回给前端
    assert "模拟内部数据库连接异常" not in (
        response.text
    )
