from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from apps.api.app.schemas.machine import (
    MachineCreate,
    MachineResponse,
    MachineUpdate,
)
from services.database.session import get_db
from services.mes.machine_service import (
    InvalidMachineStatusError,
    MachineAlreadyExistsError,
    MachineNotFoundError,
    MachineService,
)

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

    try:
        return service.get_machine(machine_id)

    except MachineNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


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

    try:
        return service.create_machine(
            machine_data.model_dump()
        )

    except MachineAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except InvalidMachineStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


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

    try:
        update_data = machine_data.model_dump(
            exclude_unset=True,
        )

        return service.update_machine(
            machine_id,
            update_data,
        )

    except MachineNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidMachineStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


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

    try:
        service.delete_machine(machine_id)

        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    except MachineNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc