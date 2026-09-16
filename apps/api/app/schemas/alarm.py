from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# 报警级别
AlarmLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class AlarmCreate(BaseModel):
    """
    创建报警时，客户端需要提交的数据
    """

    machine_id: int = Field(
        ...,
        gt=0,
        description="设备 ID",
    )

    alarm_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="报警编码，例如 E102",
    )

    alarm_message: str = Field(
        ...,
        min_length=1,
        description="报警内容",
    )

    level: AlarmLevel = Field(
        default="medium",
        description="报警级别",
    )

    started_at: datetime | None = Field(
        default=None,
        description="报警开始时间，不传则由系统生成",
    )


class AlarmResolve(BaseModel):
    """
    恢复报警时的数据

    ended_at 不传时，由 Service 使用当前时间
    """

    ended_at: datetime | None = Field(
        default=None,
        description="报警结束时间",
    )


class AlarmResponse(BaseModel):
    """
    返回给前端的报警数据
    """

    id: int

    machine_id: int

    alarm_code: str

    alarm_message: str

    level: str

    started_at: datetime

    ended_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )