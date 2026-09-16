from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.database.models.alarm import MachineAlarm


class AlarmRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[MachineAlarm]:
        """
        查询所有报警记录
        """
        stmt = (
            select(MachineAlarm)
            .order_by(MachineAlarm.started_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def find_by_id(self, alarm_id: int) -> MachineAlarm | None:
        """
        根据报警 ID 查询
        """
        stmt = (
            select(MachineAlarm)
            .where(MachineAlarm.id == alarm_id)
        )

        return self.db.scalar(stmt)

    def find_by_machine_id(
        self,
        machine_id: int,
    ) -> list[MachineAlarm]:
        """
        查询某台设备的全部报警
        """
        stmt = (
            select(MachineAlarm)
            .where(MachineAlarm.machine_id == machine_id)
            .order_by(MachineAlarm.started_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def find_active_by_machine_id(
        self,
        machine_id: int,
    ) -> list[MachineAlarm]:
        """
        查询某台设备当前未恢复报警

        ended_at IS NULL
        表示报警尚未结束
        """
        stmt = (
            select(MachineAlarm)
            .where(
                MachineAlarm.machine_id == machine_id,
                MachineAlarm.ended_at.is_(None),
            )
            .order_by(MachineAlarm.started_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def find_active(self) -> list[MachineAlarm]:
        """
        查询所有未恢复报警
        """
        stmt = (
            select(MachineAlarm)
            .where(MachineAlarm.ended_at.is_(None))
            .order_by(MachineAlarm.started_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def find_by_alarm_code(
        self,
        alarm_code: str,
    ) -> list[MachineAlarm]:
        """
        根据报警编码查询，例如 E102
        """
        stmt = (
            select(MachineAlarm)
            .where(MachineAlarm.alarm_code == alarm_code)
            .order_by(MachineAlarm.started_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def create(
        self,
        *,
        machine_id: int,
        alarm_code: str,
        alarm_message: str,
        level: str = "medium",
        started_at: datetime | None = None,
    ) -> MachineAlarm:
        """
        创建报警
        """

        alarm = MachineAlarm(
            machine_id=machine_id,
            alarm_code=alarm_code,
            alarm_message=alarm_message,
            level=level,
        )

        if started_at is not None:
            alarm.started_at = started_at

        self.db.add(alarm)

        # 把 INSERT 发给数据库，
        # 但这里先不 commit
        self.db.flush()

        # 获取数据库生成的 id 等字段
        self.db.refresh(alarm)

        return alarm

    def resolve(
        self,
        alarm: MachineAlarm,
        ended_at: datetime | None = None,
    ) -> MachineAlarm:
        """
        恢复 / 结束报警
        """
        alarm.ended_at = ended_at or datetime.utcnow()  # noqa: DTZ003

        self.db.flush()
        self.db.refresh(alarm)

        return alarm

    def delete(
        self,
        alarm: MachineAlarm,
    ) -> None:
        """
        删除报警

        V0 可以保留，
        实际企业系统通常不会轻易删除历史报警。
        """
        self.db.delete(alarm)
        self.db.flush()