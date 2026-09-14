from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.database.base import Base

if TYPE_CHECKING:
    from services.database.models.alarm import MachineAlarm
    from services.database.models.production_record import ProductionRecord
    from services.database.models.work_order import WorkOrder


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    line_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="offline",
        index=True,
    )

    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # 一台设备可以有很多条报警
    alarms: Mapped[list["MachineAlarm"]] = relationship(
        back_populates="machine",
        cascade="all, delete-orphan",
    )

    # 一台设备可以有很多张工单
    work_orders: Mapped[list["WorkOrder"]] = relationship(
        back_populates="machine",
        cascade="all, delete-orphan",
    )

    production_records: Mapped[list["ProductionRecord"]] = relationship(
    back_populates="machine",
)

    def __repr__(self) -> str:
        return (
            f"<Machine("
            f"id={self.id}, "
            f"code='{self.code}', "
            f"name='{self.name}', "
            f"status='{self.status}'"
            f")>"
        )