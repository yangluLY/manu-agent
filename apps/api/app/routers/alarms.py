from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from apps.api.app.schemas.alarm import (
    AlarmCreate,
    AlarmResolve,
    AlarmResponse,
)
from services.database.session import get_db
from services.mes.alarm_service import AlarmService

router = APIRouter(
    prefix="/api/v1/alarms",
    tags=["Alarms"],
)


@router.get(
    "",
    response_model=list[AlarmResponse],
)
def get_alarms(
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    查询报警列表。

    active_only=true 时，只查询当前未恢复报警。
    """

    service = AlarmService(db)

    if active_only:
        return service.get_active_alarms()

    return service.get_all_alarms()


@router.get(
    "/{alarm_id}",
    response_model=AlarmResponse,
)
def get_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
):
    """
    根据报警 ID 查询报警详情。
    """

    service = AlarmService(db)

    return service.get_alarm(alarm_id)


@router.post(
    "",
    response_model=AlarmResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_alarm(
    data: AlarmCreate,
    db: Session = Depends(get_db),
):
    """
    创建设备报警。
    """

    service = AlarmService(db)

    return service.create_alarm(
        machine_id=data.machine_id,
        alarm_code=data.alarm_code,
        alarm_message=data.alarm_message,
        level=data.level,
        started_at=data.started_at,
    )


@router.patch(
    "/{alarm_id}/resolve",
    response_model=AlarmResponse,
)
def resolve_alarm(
    alarm_id: int,
    data: AlarmResolve,
    db: Session = Depends(get_db),
):
    """
    恢复报警。
    """

    service = AlarmService(db)

    return service.resolve_alarm(
        alarm_id=alarm_id,
        ended_at=data.ended_at,
    )
