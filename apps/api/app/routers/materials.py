from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apps.api.app.schemas.material import (
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
    StockAdjustRequest,
    StockSetRequest,
)
from services.database.session import get_db
from services.mes.inventory_service import InventoryService

router = APIRouter(
    prefix="/api/v1/materials",
    tags=["Materials"],
)


@router.get(
    "",
    response_model=list[MaterialResponse],
)
def get_materials(
    db: Session = Depends(get_db),
):
    """
    查询全部物料。
    """

    service = InventoryService(db)

    return service.get_all_materials()


@router.get(
    "/low-stock",
    response_model=list[MaterialResponse],
)
def get_low_stock_materials(
    db: Session = Depends(get_db),
):
    """
    查询低于安全库存的物料。

    stock_qty < safe_stock
    """

    service = InventoryService(db)

    return service.get_low_stock_materials()


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
)
def get_material(
    material_id: int,
    db: Session = Depends(get_db),
):
    """
    根据 ID 查询物料。
    """

    service = InventoryService(db)

    return service.get_material(material_id)


@router.post(
    "",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_material(
    data: MaterialCreate,
    db: Session = Depends(get_db),
):
    """
    创建物料。
    """

    service = InventoryService(db)

    return service.create_material(
        code=data.code,
        name=data.name,
        unit=data.unit,
        stock_qty=data.stock_qty,
        safe_stock=data.safe_stock,
    )


@router.patch(
    "/{material_id}",
    response_model=MaterialResponse,
)
def update_material(
    material_id: int,
    data: MaterialUpdate,
    db: Session = Depends(get_db),
):
    """
    修改物料基础信息。

    只修改客户端实际提交的字段。
    """

    service = InventoryService(db)

    update_data = data.model_dump(
        exclude_unset=True,
    )

    return service.update_material(
        material_id,
        **update_data,
    )


@router.patch(
    "/{material_id}/stock/set",
    response_model=MaterialResponse,
)
def set_material_stock(
    material_id: int,
    data: StockSetRequest,
    db: Session = Depends(get_db),
):
    """
    直接设置库存。

    适合盘点修正场景。
    """

    service = InventoryService(db)

    return service.set_stock(
        material_id=material_id,
        stock_qty=data.stock_qty,
    )


@router.patch(
    "/{material_id}/stock/adjust",
    response_model=MaterialResponse,
)
def adjust_material_stock(
    material_id: int,
    data: StockAdjustRequest,
    db: Session = Depends(get_db),
):
    """
    调整库存。

    quantity_change > 0：入库
    quantity_change < 0：出库
    """

    service = InventoryService(db)

    return service.adjust_stock(
        material_id=material_id,
        quantity_change=data.quantity_change,
    )
