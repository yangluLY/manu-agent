
import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from agent.workflow.persistence.thread_store import (
    WorkflowAccessDenied,
    WorkflowThreadConflict,
    WorkflowThreadStore,
)

load_dotenv()

@pytest.fixture
def store():
    dsn = os.getenv("TEST_APPROVAL_DSN")

    if not dsn:
        pytest.skip(
            "未配置 TEST_APPROVAL_DSN"
        )

    return WorkflowThreadStore(dsn=dsn)


def test_register_owner(store):
    thread_id = str(uuid4())

    store.register(thread_id, "user-001")

    assert store.get_owner(thread_id) == (
        "user-001"
    )


def test_register_idempotent(store):
    thread_id = str(uuid4())

    store.register(thread_id, "user-001")
    store.register(thread_id, "user-001")

    assert store.get_owner(thread_id) == (
        "user-001"
    )


def test_register_conflict(store):
    thread_id = str(uuid4())

    store.register(thread_id, "user-001")

    with pytest.raises(WorkflowThreadConflict):
        store.register(
            thread_id,
            "user-002",
        )


def test_owner_access(store):
    thread_id = str(uuid4())

    store.register(thread_id, "user-001")

    store.assert_owner(
        thread_id,
        "user-001",
    )


def test_cross_user_denied(store):
    thread_id = str(uuid4())

    store.register(thread_id, "user-001")

    with pytest.raises(WorkflowAccessDenied):
        store.assert_owner(
            thread_id,
            "user-002",
        )


def test_unknown_thread_denied(store):
    with pytest.raises(WorkflowAccessDenied):
        store.assert_owner(
            str(uuid4()),
            "user-001",
        )


def test_invalid_id(store):
    with pytest.raises(ValueError):
        store.register("", "user-001")
