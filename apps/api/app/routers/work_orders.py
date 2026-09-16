from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apps.api.app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderResponse,
    WorkOrderUpdate,
)
from services.database.session import get_db
from services.mes.work_order_service import WorkOrderService

router = APIRouter(
    prefix="/api/v1/work-orders",
    tags=["Work Orders"],
)


@router.get(
    "",
    response_model=list[WorkOrderResponse],
)
def get_work_orders(
    db: Session = Depends(get_db),
):
    """
    查询全部工单。
    """

    service = WorkOrderService(db)

    return service.get_all_work_orders()


@router.get(
    "/{work_order_id}",
    response_model=WorkOrderResponse,
)
def get_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
):
    """
    根据 ID 查询工单。
    """

    service = WorkOrderService(db)

    return service.get_work_order(work_order_id)


@router.post(
    "",
    response_model=WorkOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_work_order(
    data: WorkOrderCreate,
    db: Session = Depends(get_db),
):
    """
    创建工单。
    """

    service = WorkOrderService(db)

    return service.create_work_order(
        machine_id=data.machine_id,
        type=data.type,
        priority=data.priority,
        description=data.description,
        assigned_to=data.assigned_to,
    )


@router.patch(
    "/{work_order_id}",
    response_model=WorkOrderResponse,
)
def update_work_order(
    work_order_id: int,
    data: WorkOrderUpdate,
    db: Session = Depends(get_db),
):
    """
    修改工单。

    只修改客户端实际传入的字段。
    """

    service = WorkOrderService(db)

    update_data = data.model_dump(
        exclude_unset=True
    )

    return service.update_work_order(
        work_order_id,
        **update_data,
    )


@router.patch(
    "/{work_order_id}/complete",
    response_model=WorkOrderResponse,
)
def complete_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
):
    """
    完成工单。
    """

    service = WorkOrderService(db)

    return service.complete_work_order(work_order_id)


@router.patch(
    "/{work_order_id}/cancel",
    response_model=WorkOrderResponse,
)
def cancel_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
):
    """
    取消工单。
    """

    service = WorkOrderService(db)

    return service.cancel_work_order(work_order_id)
