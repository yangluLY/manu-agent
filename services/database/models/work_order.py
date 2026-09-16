from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.database.base import Base
from services.database.models.machine import Machine


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # 工单编号，例如 WO-20260914-001
    order_no: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    # 对应设备
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 工单类型
    # maintenance / repair / inspection
    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="maintenance",
    )

    # 优先级
    # low / medium / high / urgent
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )

    # 工单描述
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 工单状态
    # pending / in_progress / completed / cancelled
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    # 负责人
    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
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

    # ORM 关系
    machine: Mapped["Machine"] = relationship(
        back_populates="work_orders"
    )

    def __repr__(self) -> str:
        return (
            f"<WorkOrder("
            f"id={self.id}, "
            f"order_no='{self.order_no}', "
            f"status='{self.status}', "
            f"priority='{self.priority}'"
            f")>"
        )