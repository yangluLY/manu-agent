from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from services.database.base import Base


class Material(Base):
    __tablename__ = "materials"

    __table_args__ = (
        CheckConstraint(
            "stock_qty >= 0",
            name="ck_material_stock_qty_non_negative",
        ),
        CheckConstraint(
            "safe_stock >= 0",
            name="ck_material_safe_stock_non_negative",
        ),
    )

    # 数据库主键
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # 物料编码，例如 MAT-001
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    # 物料名称，例如 铝合金板材
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # 单位，例如 kg / L / pcs
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # 当前库存
    stock_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # 安全库存
    safe_stock: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
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

    def __repr__(self) -> str:
        return (
            f"<Material("
            f"id={self.id}, "
            f"code='{self.code}', "
            f"name='{self.name}', "
            f"stock_qty={self.stock_qty}, "
            f"safe_stock={self.safe_stock}"
            f")>"
        )