from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from apps.api.app.schemas.alarm import AlarmResponse
from apps.api.app.schemas.machine import (
    MachineCreate,
    MachineResponse,
    MachineUpdate,
)
from services.database.session import get_db
from services.mes.alarm_service import AlarmService
from services.mes.machine_service import MachineService

router = APIRouter(
    prefix="/api/v1/machines",
    tags=["Machines"],
)


@router.get(
    "",
    response_model=list[MachineResponse],
)
def get_machines(
    db: Session = Depends(get_db),
):
    """
    获取所有设备
    """
    service = MachineService(db)

    return service.get_machines()


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
)
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db),
):
    """
    根据 ID 获取设备详情
    """
    service = MachineService(db)

    return service.get_machine(machine_id)


@router.post(
    "",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_machine(
    machine_data: MachineCreate,
    db: Session = Depends(get_db),
):
    """
    创建设备
    """
    service = MachineService(db)

    return service.create_machine(
        machine_data.model_dump()
    )


@router.put(
    "/{machine_id}",
    response_model=MachineResponse,
)
def update_machine(
    machine_id: int,
    machine_data: MachineUpdate,
    db: Session = Depends(get_db),
):
    """
    更新设备
    """
    service = MachineService(db)

    update_data = machine_data.model_dump(
        exclude_unset=True,
    )

    return service.update_machine(
        machine_id,
        update_data,
    )


@router.delete(
    "/{machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_machine(
    machine_id: int,
    db: Session = Depends(get_db),
):
    """
    删除设备
    """
    service = MachineService(db)

    service.delete_machine(machine_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get(
    "/machine/{machine_id}",
    response_model=list[AlarmResponse],
)
def get_machine_alarms(
    machine_id: int,
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    查询指定设备的报警记录。
    """

    service = AlarmService(db)

    if active_only:
        return service.get_active_machine_alarms(machine_id)

    return service.get_machine_alarms(machine_id)
