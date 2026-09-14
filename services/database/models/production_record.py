from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.database.base import Base

if TYPE_CHECKING:
    from services.database.models.machine import Machine


class ProductionRecord(Base):
    __tablename__ = "production_records"

    __table_args__ = (
        CheckConstraint(
            "planned_qty >= 0",
            name="ck_production_planned_qty_non_negative",
        ),
        CheckConstraint(
            "actual_qty >= 0",
            name="ck_production_actual_qty_non_negative",
        ),
        CheckConstraint(
            "defect_qty >= 0",
            name="ck_production_defect_qty_non_negative",
        ),
        CheckConstraint(
            "defect_qty <= actual_qty",
            name="ck_production_defect_not_greater_than_actual",
        ),
    )

    # 数据库主键
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # 哪台设备产生的生产记录
    machine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "machines.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # 产线编码
    # V0 暂时不建立 production_lines 表
    line_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # 产品编码
    # V0 暂时不建立 products 表
    product_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # 计划生产数量
    planned_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # 实际生产数量
    actual_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # 不良品数量
    defect_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # 生产日期
    production_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # ORM 关系
    machine: Mapped["Machine"] = relationship(
        back_populates="production_records",
    )

    def __repr__(self) -> str:
        return (
            f"<ProductionRecord("
            f"id={self.id}, "
            f"machine_id={self.machine_id}, "
            f"line_code='{self.line_code}', "
            f"product_code='{self.product_code}', "
            f"production_date='{self.production_date}'"
            f")>"
        )