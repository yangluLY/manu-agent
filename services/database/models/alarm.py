from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.database.base import Base
from services.database.models.machine import Machine


class MachineAlarm(Base):
    __tablename__ = "machine_alarms"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # 哪一台设备发生的报警
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 报警编码，例如 E101
    alarm_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # 报警内容，例如：主轴温度过高
    alarm_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 报警级别，例如 low / medium / high / critical
    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )

    # 报警开始时间
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # 报警结束时间
    # None 表示报警还没有恢复
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # ORM 关系
    machine: Mapped["Machine"] = relationship(
        back_populates="alarms"
    )

    def __repr__(self) -> str:
        return (
            f"<MachineAlarm("
            f"id={self.id}, "
            f"machine_id={self.machine_id}, "
            f"alarm_code='{self.alarm_code}', "
            f"level='{self.level}'"
            f")>"
        )