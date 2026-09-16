from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from apps.api.app.schemas.production_record import (
    ProductionMetricsResponse,
    ProductionRecordCreate,
    ProductionRecordResponse,
    ProductionRecordUpdate,
    ProductionSummaryResponse,
)
from services.database.session import get_db
from services.mes.production_service import ProductionService

router = APIRouter(
    prefix="/api/v1/production-records",
    tags=["Production Records"],
)


@router.get(
    "",
    response_model=list[ProductionRecordResponse],
)
def get_production_records(
    machine_id: int | None = Query(
        default=None,
        gt=0,
        description="设备 ID",
    ),
    line_code: str | None = Query(
        default=None,
        description="产线编码，例如 LINE-A",
    ),
    product_code: str | None = Query(
        default=None,
        description="产品编码，例如 PRODUCT-A01",
    ),
    start_date: date | None = Query(
        default=None,
        description="开始日期",
    ),
    end_date: date | None = Query(
        default=None,
        description="结束日期",
    ),
    db: Session = Depends(get_db),
):
    """
    查询生产记录。

    支持按：
    - 设备
    - 产线
    - 产品
    - 日期范围

    组合筛选。
    """

    service = ProductionService(db)

    return service.get_records(
        machine_id=machine_id,
        line_code=line_code,
        product_code=product_code,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/summary",
    response_model=ProductionSummaryResponse,
)
def get_production_summary(
    machine_id: int | None = Query(
        default=None,
        gt=0,
    ),
    line_code: str | None = Query(
        default=None,
    ),
    product_code: str | None = Query(
        default=None,
    ),
    start_date: date | None = Query(
        default=None,
    ),
    end_date: date | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
):
    """
    查询生产数据汇总 KPI。
    """

    service = ProductionService(db)

    return service.get_summary(
        machine_id=machine_id,
        line_code=line_code,
        product_code=product_code,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{record_id}/metrics",
    response_model=ProductionMetricsResponse,
)
def get_production_metrics(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    查询单条生产记录的 KPI。
    """

    service = ProductionService(db)

    return service.get_record_metrics(record_id)


@router.get(
    "/{record_id}",
    response_model=ProductionRecordResponse,
)
def get_production_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    根据 ID 查询生产记录。
    """

    service = ProductionService(db)

    return service.get_record(record_id)


@router.post(
    "",
    response_model=ProductionRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_production_record(
    data: ProductionRecordCreate,
    db: Session = Depends(get_db),
):
    """
    创建生产记录。
    """

    service = ProductionService(db)

    return service.create_record(
        machine_id=data.machine_id,
        line_code=data.line_code,
        product_code=data.product_code,
        planned_qty=data.planned_qty,
        actual_qty=data.actual_qty,
        defect_qty=data.defect_qty,
        production_date=data.production_date,
    )


@router.patch(
    "/{record_id}",
    response_model=ProductionRecordResponse,
)
def update_production_record(
    record_id: int,
    data: ProductionRecordUpdate,
    db: Session = Depends(get_db),
):
    """
    修改生产记录。

    只修改客户端实际提交的字段。
    """

    service = ProductionService(db)

    update_data = data.model_dump(
        exclude_unset=True,
    )

    return service.update_record(
        record_id,
        **update_data,
    )
