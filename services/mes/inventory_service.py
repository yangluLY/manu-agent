from decimal import Decimal

from sqlalchemy.orm import Session

from apps.api.app.core.exceptions import (
    InsufficientInventoryException,
    InvalidInventoryQuantityException,
    MaterialCodeExistsException,
    MaterialNotFoundException,
)
from services.database.models.material import Material
from services.database.repositories.material_repository import MaterialRepository


class InventoryService:

    def __init__(self, db: Session):
        self.db = db
        self.material_repo = MaterialRepository(db)

    def get_all_materials(self) -> list[Material]:
        """
        查询所有物料
        """
        return self.material_repo.find_all()

    def get_material(
        self,
        material_id: int,
    ) -> Material:
        """
        根据数据库 ID 查询物料
        """

        material = self.material_repo.find_by_id(material_id)

        if material is None:
            raise MaterialNotFoundException()

        return material

    def get_material_by_code(
        self,
        code: str,
    ) -> Material:
        """
        根据物料编码查询

        例如：
        MAT-001
        """

        material = self.material_repo.find_by_code(code)

        if material is None:
            raise MaterialNotFoundException()

        return material

    def get_low_stock_materials(self) -> list[Material]:
        """
        查询低库存物料

        stock_qty < safe_stock
        """
        return self.material_repo.find_low_stock()

    def create_material(
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

        # 物料编码不能重复
        existing_material = self.material_repo.find_by_code(code)

        if existing_material is not None:
            raise MaterialCodeExistsException()

        # 业务层先校验，避免等数据库约束报错
        if stock_qty < 0:
            raise InvalidInventoryQuantityException(
                "Stock quantity cannot be negative"
            )

        if safe_stock < 0:
            raise InvalidInventoryQuantityException(
                "Safe stock cannot be negative"
            )

        try:
            material = self.material_repo.create(
                code=code,
                name=name,
                unit=unit,
                stock_qty=stock_qty,
                safe_stock=safe_stock,
            )

            self.db.commit()
            self.db.refresh(material)

            return material

        except Exception:
            self.db.rollback()
            raise

    def update_material(
        self,
        material_id: int,
        **data,
    ) -> Material:
        """
        修改物料信息
        """

        material = self.material_repo.find_by_id(material_id)

        if material is None:
            raise MaterialNotFoundException()

        if "stock_qty" in data:
            stock_qty = data["stock_qty"]

            if stock_qty is not None and stock_qty < 0:
                raise InvalidInventoryQuantityException(
                    "Stock quantity cannot be negative"
                )

        if "safe_stock" in data:
            safe_stock = data["safe_stock"]

            if safe_stock is not None and safe_stock < 0:
                raise InvalidInventoryQuantityException(
                    "Safe stock cannot be negative"
                )

        try:
            material = self.material_repo.update(
                material,
                **data,
            )

            self.db.commit()
            self.db.refresh(material)

            return material

        except Exception:
            self.db.rollback()
            raise

    def set_stock(
        self,
        material_id: int,
        stock_qty: Decimal,
    ) -> Material:
        """
        直接设置库存数量。

        例如盘点后：
        当前系统库存 100
        实际盘点库存 95
        则可以直接设置为 95。
        """

        material = self.material_repo.find_by_id(material_id)

        if material is None:
            raise MaterialNotFoundException()

        if stock_qty < 0:
            raise InvalidInventoryQuantityException(
                "Stock quantity cannot be negative"
            )

        try:
            material = self.material_repo.update_stock(
                material,
                stock_qty,
            )

            self.db.commit()
            self.db.refresh(material)

            return material

        except Exception:
            self.db.rollback()
            raise

    def adjust_stock(
        self,
        material_id: int,
        quantity_change: Decimal,
    ) -> Material:
        """
        增加或减少库存。

        quantity_change > 0：
            入库

        quantity_change < 0：
            出库

        示例：
            +100  入库 100
            -20   出库 20
        """

        material = self.material_repo.find_by_id(material_id)

        if material is None:
            raise MaterialNotFoundException()

        new_stock = (
            material.stock_qty
            + quantity_change
        )

        if new_stock < 0:
            raise InsufficientInventoryException()

        try:
            material = self.material_repo.update_stock(
                material,
                new_stock,
            )

            self.db.commit()
            self.db.refresh(material)

            return material

        except Exception:
            self.db.rollback()
            raise
