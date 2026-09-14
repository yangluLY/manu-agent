from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WorkOrderType = Literal[
    "maintenance",
    "repair",
    "inspection",
]

WorkOrderPriority = Literal[
    "low",
    "medium",
    "high",
    "urgent",
]

WorkOrderStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "cancelled",
]


class WorkOrderCreate(BaseModel):
    """
    创建工单
    """

    machine_id: int = Field(
        ...,
        gt=0,
        description="设备 ID",
    )

    type: WorkOrderType = Field(
        default="maintenance",
        description="工单类型",
    )

    priority: WorkOrderPriority = Field(
        default="medium",
        description="工单优先级",
    )

    description: str = Field(
        ...,
        min_length=1,
        description="工单描述",
    )

    assigned_to: str | None = Field(
        default=None,
        max_length=100,
        description="工单负责人",
    )


class WorkOrderUpdate(BaseModel):
    """
    修改工单。

    所有字段都是可选的，
    只修改客户端实际提交的字段。
    """

    type: WorkOrderType | None = None

    priority: WorkOrderPriority | None = None

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    status: WorkOrderStatus | None = None

    assigned_to: str | None = Field(
        default=None,
        max_length=100,
    )


class WorkOrderResponse(BaseModel):
    """
    返回给前端的完整工单
    """

    id: int

    order_no: str

    machine_id: int

    type: str

    priority: str

    description: str

    status: str

    assigned_to: str | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )