from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductionRecordCreate(BaseModel):
    """
    创建生产记录
    """

    machine_id: int = Field(
        ...,
        gt=0,
        description="设备 ID",
    )

    line_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="产线编码，例如 LINE-A",
    )

    product_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="产品编码，例如 PRODUCT-A01",
    )

    planned_qty: int = Field(
        ...,
        ge=0,
        description="计划生产数量",
    )

    actual_qty: int = Field(
        ...,
        ge=0,
        description="实际生产数量",
    )

    defect_qty: int = Field(
        default=0,
        ge=0,
        description="不良品数量",
    )

    production_date: date = Field(
        ...,
        description="生产日期",
    )


class ProductionRecordUpdate(BaseModel):
    """
    修改生产记录
    """

    machine_id: int | None = Field(
        default=None,
        gt=0,
    )

    line_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    product_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    planned_qty: int | None = Field(
        default=None,
        ge=0,
    )

    actual_qty: int | None = Field(
        default=None,
        ge=0,
    )

    defect_qty: int | None = Field(
        default=None,
        ge=0,
    )

    production_date: date | None = None


class ProductionRecordResponse(BaseModel):
    """
    返回生产记录
    """

    id: int
    machine_id: int
    line_code: str
    product_code: str

    planned_qty: int
    actual_qty: int
    defect_qty: int

    production_date: date
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductionMetricsResponse(BaseModel):
    """
    单条生产记录 KPI
    """

    record_id: int
    machine_id: int

    line_code: str
    product_code: str

    production_date: date

    planned_qty: int
    actual_qty: int
    defect_qty: int

    completion_rate: float = Field(
        description="生产完成率，单位 %",
    )

    defect_rate: float = Field(
        description="不良率，单位 %",
    )


class ProductionSummaryResponse(BaseModel):
    """
    生产数据汇总
    """

    record_count: int

    planned_qty: int
    actual_qty: int
    defect_qty: int

    completion_rate: float = Field(
        description="汇总生产完成率，单位 %",
    )

    defect_rate: float = Field(
        description="汇总不良率，单位 %",
    )