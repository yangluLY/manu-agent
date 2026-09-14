from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.database.models.material import Material


class MaterialRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[Material]:
        """
        查询全部物料
        """
        stmt = (
            select(Material)
            .order_by(Material.code.asc())
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def find_by_id(
        self,
        material_id: int,
    ) -> Material | None:
        """
        根据数据库主键 ID 查询物料
        """
        return self.db.get(Material, material_id)

    def find_by_code(
        self,
        code: str,
    ) -> Material | None:
        """
        根据物料编码查询物料，例如 MAT-001
        """
        stmt = (
            select(Material)
            .where(Material.code == code)
        )

        result = self.db.execute(stmt)

        return result.scalar_one_or_none()

    def find_low_stock(self) -> list[Material]:
        """
        查询库存低于安全库存的物料

        stock_qty < safe_stock
        """
        stmt = (
            select(Material)
            .where(
                Material.stock_qty < Material.safe_stock
            )
            .order_by(Material.stock_qty.asc())
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def create(
        self,
        *,
        code: str,
        name: str,
        unit: str,
        stock_qty: Decimal = Decimal("0.00"),
        safe_stock: Decimal = Decimal("0.00"),
    ) -> Material:
        """
        创建物料
        """

        material = Material(
            code=code,
            name=name,
            unit=unit,
            stock_qty=stock_qty,
            safe_stock=safe_stock,
        )

        self.db.add(material)

        # 发送 INSERT，但不提交事务
        self.db.flush()

        # 获取数据库生成的 id 等信息
        self.db.refresh(material)

        return material

    def update(
        self,
        material: Material,
        **data,
    ) -> Material:
        """
        更新物料基础信息
        """

        allowed_fields = {
            "name",
            "unit",
            "stock_qty",
            "safe_stock",
        }

        for field, value in data.items():
            if field in allowed_fields:
                setattr(material, field, value)

        self.db.flush()
        self.db.refresh(material)

        return material

    def update_stock(
        self,
        material: Material,
        stock_qty: Decimal,
    ) -> Material:
        """
        直接修改当前库存
        """

        material.stock_qty = stock_qty

        self.db.flush()
        self.db.refresh(material)

        return material

    def delete(
        self,
        material: Material,
    ) -> None:
        """
        删除物料

        V0 学习阶段可以保留。
        后续真实系统一般更适合停用，而不是物理删除。
        """

        self.db.delete(material)
        self.db.flush()