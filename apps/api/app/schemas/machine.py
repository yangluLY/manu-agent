from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MachineBase(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=50,
        examples=["CNC-001"],
    )

    name: str = Field(
        min_length=1,
        max_length=100,
        examples=["1号数控加工中心"],
    )

    model: str | None = Field(
        default=None,
        max_length=100,
        examples=["VMC850"],
    )

    line_code: str | None = Field(
        default=None,
        max_length=50,
        examples=["LINE-A"],
    )

    status: str = Field(
        default="offline",
        max_length=30,
        examples=["running"],
    )


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    model: str | None = Field(
        default=None,
        max_length=100,
    )

    line_code: str | None = Field(
        default=None,
        max_length=50,
    )

    status: str | None = Field(
        default=None,
        max_length=30,
    )

    last_heartbeat_at: datetime | None = None


class MachineResponse(MachineBase):
    id: int
    last_heartbeat_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )