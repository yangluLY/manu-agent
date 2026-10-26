
"""
ManuAgent V4.8.2

LangGraph updates -> SSE events
"""

import json
import logging
from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel

from agent.workflow.mappers.response_mapper import (
    build_workflow_response,
)
from agent.workflow.persistence.postgres import (
    build_thread_config,
)

logger = logging.getLogger(__name__)


def encode_sse(
    event: str,
    data: dict[str, Any],
) -> str:
    """
    编码标准 SSE 消息。

    格式：
    event: workflow_started
    data: {...}

    两个换行表示一条完整消息。
    """

    payload = json.dumps(
        data,
        ensure_ascii=False,
        default=str,
        separators=(",", ":"),
    )

    return (
        f"event: {event}\n"
        f"data: {payload}\n\n"
    )


def normalize_update(
    value: Any,
) -> dict:
    """
    将 LangGraph 节点更新转换成字典。
    """

    if value is None:
        return {}

    if isinstance(value, BaseModel):
        return value.model_dump(
            mode="json"
        )

    if isinstance(value, dict):
        return value

    raise TypeError(
        "不支持的 Workflow State 更新类型"
    )


def stream_workflow_events(
    *,
    workflow: Any,
    message: str,
    thread_id: str,
    initial_state: dict,
) -> Iterator[str]:
    """
    将 LangGraph 同步 stream 转成 SSE。

    当前使用 stream_mode='updates'，
    返回节点级执行进度。

    不暴露原始数据库异常或完整内部状态。
    """

    config = build_thread_config(
        thread_id
    )

    # 用于累积各 Node 返回的状态更新
    current_state = dict(initial_state)

    # 防止多次发送同一条完成事件
    last_step_signature = None

    yield encode_sse(
        "workflow_started",
        {
            "thread_id": thread_id,
            "status": "running",
            "message": "工作流已启动",
        },
    )

    try:
        for chunk in workflow.stream(
            initial_state,
            config=config,
            stream_mode="updates",
        ):
            if not isinstance(chunk, dict):
                continue

            for node_name, raw_update in chunk.items():

                # LangGraph interrupt 单独处理
                if node_name == "__interrupt__":
                    yield encode_sse(
                        "workflow_failed",
                        {
                            "thread_id": thread_id,
                            "code": "APPROVAL_REQUIRED",
                            "message": (
                                "工作流进入人工审批等待状态，"
                                "请使用审批接口继续。"
                            ),
                        },
                    )
                    return

                update = normalize_update(
                    raw_update
                )

                # V4 State 使用覆盖式字段更新
                current_state.update(update)

                if node_name == "router":
                    yield encode_sse(
                        "route_completed",
                        {
                            "thread_id": thread_id,
                            "route": current_state.get(
                                "route"
                            ),
                            "route_reason": (
                                current_state.get(
                                    "route_reason",
                                    "",
                                )
                            ),
                        },
                    )

                elif node_name in {
                    "simple_planner",
                    "planner",
                }:
                    plan = current_state.get(
                        "plan",
                        [],
                    )

                    steps = []

                    for step in plan:
                        if isinstance(step, BaseModel):
                            step_data = step.model_dump(
                                mode="json"
                            )
                        elif isinstance(step, dict):
                            step_data = step
                        else:
                            continue

                        steps.append({
                            "id": step_data.get("id"),
                            "agent": step_data.get("agent"),
                            "task": step_data.get("task"),
                        })

                    yield encode_sse(
                        "plan_created",
                        {
                            "thread_id": thread_id,
                            "total_steps": len(steps),
                            "steps": steps,
                        },
                    )

                elif node_name in {
                    "step_executor",
                    "general",
                }:
                    results = current_state.get(
                        "step_results",
                        [],
                    )

                    if not results:
                        continue

                    step = results[-1]

                    signature = (
                        step.get("step_id"),
                        step.get("agent"),
                        len(results),
                    )

                    if signature == last_step_signature:
                        continue

                    last_step_signature = signature

                    status = step.get(
                        "status",
                        "failed",
                    )

                    event_type = (
                        "step_completed"
                        if status == "success"
                        else "step_failed"
                    )

                    # 这里只传输前端进度必需字段。
                    # 详细来源、SQL、ECharts 放在最终结果。
                    event_data = {
                        "thread_id": thread_id,
                        "step_id": step.get("step_id"),
                        "agent": step.get("agent"),
                        "status": status,
                        "duration_ms": step.get(
                            "duration_ms"
                        ),
                        "attempts": step.get(
                            "attempts",
                            1,
                        ),
                    }

                    if status == "failed":
                        error = step.get("error") or {}
                        event_data["error_code"] = (
                            error.get("code")
                        )

                    yield encode_sse(
                        event_type,
                        event_data,
                    )

        # 工作流结束后，对累计状态进行统一映射。
        # 不需要再次 invoke()，避免重复执行。
        response = build_workflow_response(
            current_state
        )

        payload = response.model_dump(
            mode="json"
        )

        payload["thread_id"] = thread_id

        final_event = (
            "workflow_completed"
            if response.status == "completed"
            else "workflow_failed"
        )

        yield encode_sse(
            final_event,
            payload,
        )

    except Exception:
        logger.exception(
            "Workflow SSE failed; thread_id=%s",
            thread_id,
        )

        yield encode_sse(
            "workflow_failed",
            {
                "thread_id": thread_id,
                "code": "WORKFLOW_EXECUTION_ERROR",
                "message": (
                    "工作流执行异常，请稍后重试。"
                ),
            },
        )
