from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any


def to_json_value(value: Any) -> Any:
    """Convert common domain values into stable JSON-compatible values."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_machine(machine: Any) -> dict[str, Any]:
    return {
        "id": machine.id,
        "code": machine.code,
        "name": machine.name,
        "model": machine.model,
        "line_code": machine.line_code,
        "status": to_json_value(machine.status),
        "last_heartbeat_at": to_json_value(machine.last_heartbeat_at),
    }


def serialize_alarm(
    alarm: Any,
    *,
    machine_code: str | None = None,
) -> dict[str, Any]:
    return {
        "id": alarm.id,
        "machine_id": alarm.machine_id,
        "machine_code": machine_code,
        "alarm_code": alarm.alarm_code,
        "alarm_message": alarm.alarm_message,
        "level": to_json_value(alarm.level),
        "started_at": to_json_value(alarm.started_at),
        "ended_at": to_json_value(alarm.ended_at),
        "active": alarm.ended_at is None,
    }


def serialize_material(material: Any) -> dict[str, Any]:
    stock_qty = Decimal(material.stock_qty)
    safe_stock = Decimal(material.safe_stock)

    return {
        "id": material.id,
        "code": material.code,
        "name": material.name,
        "unit": material.unit,
        "stock_qty": to_json_value(stock_qty),
        "safe_stock": to_json_value(safe_stock),
        "low_stock": stock_qty < safe_stock,
        "shortage_qty": to_json_value(max(safe_stock - stock_qty, Decimal("0"))),
    }


def serialize_work_order(
    work_order: Any,
    *,
    machine_code: str | None = None,
) -> dict[str, Any]:
    return {
        "id": work_order.id,
        "order_no": work_order.order_no,
        "machine_id": work_order.machine_id,
        "machine_code": machine_code,
        "type": to_json_value(work_order.type),
        "priority": to_json_value(work_order.priority),
        "description": work_order.description,
        "status": to_json_value(work_order.status),
        "assigned_to": work_order.assigned_to,
        "created_at": to_json_value(work_order.created_at),
        "updated_at": to_json_value(work_order.updated_at),
    }

def serialize_knowledge_search_result(
    result: Any,
) -> dict[str, Any]:
    """
    将知识库向量检索结果转换成稳定的 JSON 结构。
    """

    return {
        "chunk_id": result.chunk_id,
        "document_id": result.document_id,
        "document_name": result.document_name,
        "chunk_index": result.chunk_index,
        "score": round(
            float(result.score),
            4,
        ),
        "content": result.content,
        "metadata": result.metadata,
    }

