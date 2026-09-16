from datetime import datetime

from sqlalchemy.orm import Session

from apps.api.app.core.exceptions import (
    AlarmAlreadyResolvedException,
    AlarmNotFoundException,
    MachineNotFoundException,
)
from services.database.models.alarm import MachineAlarm
from services.database.repositories.alarm_repository import AlarmRepository
from services.database.repositories.machine_repository import MachineRepository


class AlarmService:

    def __init__(self, db: Session):
        self.db = db
        self.alarm_repo = AlarmRepository(db)
        self.machine_repo = MachineRepository(db)

    def get_all_alarms(self) -> list[MachineAlarm]:
        """
        查询全部报警
        """
        return self.alarm_repo.find_all()

    def get_alarm(self, alarm_id: int) -> MachineAlarm:
        """
        根据报警 ID 查询
        """
        alarm = self.alarm_repo.find_by_id(alarm_id)

        if alarm is None:
            raise AlarmNotFoundException()

        return alarm

    def get_machine_alarms(
        self,
        machine_id: int,
    ) -> list[MachineAlarm]:
        """
        查询某台设备的全部报警
        """

        machine = self.machine_repo.find_by_id(machine_id)

        if machine is None:
            raise MachineNotFoundException()

        return self.alarm_repo.find_by_machine_id(machine_id)

    def get_active_alarms(
        self,
    ) -> list[MachineAlarm]:
        """
        查询所有当前未恢复报警
        """
        return self.alarm_repo.find_active()

    def get_active_machine_alarms(
        self,
        machine_id: int,
    ) -> list[MachineAlarm]:
        """
        查询某台设备当前未恢复报警
        """

        machine = self.machine_repo.find_by_id(machine_id)

        if machine is None:
            raise MachineNotFoundException()

        return self.alarm_repo.find_active_by_machine_id(machine_id)

    def create_alarm(
        self,
        *,
        machine_id: int,
        alarm_code: str,
        alarm_message: str,
        level: str = "medium",
        started_at: datetime | None = None,
    ) -> MachineAlarm:
        """
        创建设备报警
        """

        machine = self.machine_repo.find_by_id(machine_id)

        if machine is None:
            raise MachineNotFoundException()

        try:
            alarm = self.alarm_repo.create(
                machine_id=machine_id,
                alarm_code=alarm_code,
                alarm_message=alarm_message,
                level=level,
                started_at=started_at,
            )

            self.db.commit()
            self.db.refresh(alarm)

            return alarm

        except Exception:
            self.db.rollback()
            raise

    def resolve_alarm(
        self,
        alarm_id: int,
        ended_at: datetime | None = None,
    ) -> MachineAlarm:
        """
        恢复报警
        """

        alarm = self.alarm_repo.find_by_id(alarm_id)

        if alarm is None:
            raise AlarmNotFoundException()

        if alarm.ended_at is not None:
            raise AlarmAlreadyResolvedException()

        try:
            alarm = self.alarm_repo.resolve(
                alarm=alarm,
                ended_at=ended_at,
            )

            self.db.commit()
            self.db.refresh(alarm)

            return alarm

        except Exception:
            self.db.rollback()
            raise
