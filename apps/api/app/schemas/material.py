from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MaterialCreate(BaseModel):
    """
    创建物料
    """

    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="物料编码，例如 MAT-001",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="物料名称",
    )

    unit: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="计量单位，例如 kg / L / pcs",
    )

    stock_qty: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="当前库存数量",
    )

    safe_stock: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="安全库存数量",
    )


class MaterialUpdate(BaseModel):
    """
    修改物料。

    所有字段可选，只更新客户端实际提交的字段。
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    stock_qty: Decimal | None = Field(
        default=None,
        ge=0,
    )

    safe_stock: Decimal | None = Field(
        default=None,
        ge=0,
    )


class StockSetRequest(BaseModel):
    """
    直接设置库存。

    适合盘点后的库存修正。
    """

    stock_qty: Decimal = Field(
        ...,
        ge=0,
        description="新的库存数量",
    )


class StockAdjustRequest(BaseModel):
    """
    调整库存。

    正数：入库
    负数：出库
    """

    quantity_change: Decimal = Field(
        ...,
        description="库存变化量，例如 100 或 -20",
    )


class MaterialResponse(BaseModel):
    """
    返回给前端的物料数据
    """

    id: int
    code: str
    name: str
    unit: str
    stock_qty: Decimal
    safe_stock: Decimal

    model_config = ConfigDict(
        from_attributes=True,
    )