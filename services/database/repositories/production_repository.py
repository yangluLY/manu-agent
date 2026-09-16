from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.database.models.production_record import ProductionRecord


class ProductionRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[ProductionRecord]:
        """
        查询全部生产记录
        """
        stmt = (
            select(ProductionRecord)
            .order_by(
                ProductionRecord.production_date.desc(),
                ProductionRecord.id.desc(),
            )
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def find_by_id(
        self,
        production_record_id: int,
    ) -> ProductionRecord | None:
        """
        根据数据库主键 ID 查询生产记录
        """
        return self.db.get(
            ProductionRecord,
            production_record_id,
        )

    def find_by_machine_id(
        self,
        machine_id: int,
    ) -> list[ProductionRecord]:
        """
        查询指定设备的生产记录
        """
        stmt = (
            select(ProductionRecord)
            .where(
                ProductionRecord.machine_id == machine_id
            )
            .order_by(
                ProductionRecord.production_date.desc()
            )
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def find_by_line_code(
        self,
        line_code: str,
    ) -> list[ProductionRecord]:
        """
        查询指定产线的生产记录
        """
        stmt = (
            select(ProductionRecord)
            .where(
                ProductionRecord.line_code == line_code
            )
            .order_by(
                ProductionRecord.production_date.desc()
            )
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def find_by_product_code(
        self,
        product_code: str,
    ) -> list[ProductionRecord]:
        """
        查询指定产品的生产记录
        """
        stmt = (
            select(ProductionRecord)
            .where(
                ProductionRecord.product_code == product_code
            )
            .order_by(
                ProductionRecord.production_date.desc()
            )
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def find_by_date(
        self,
        production_date: date,
    ) -> list[ProductionRecord]:
        """
        查询指定日期的生产记录
        """
        stmt = (
            select(ProductionRecord)
            .where(
                ProductionRecord.production_date
                == production_date
            )
            .order_by(ProductionRecord.id.asc())
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[ProductionRecord]:
        """
        查询日期范围内的生产记录。

        包含 start_date 和 end_date。
        """
        stmt = (
            select(ProductionRecord)
            .where(
                ProductionRecord.production_date
                >= start_date,
                ProductionRecord.production_date
                <= end_date,
            )
            .order_by(
                ProductionRecord.production_date.asc()
            )
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def find_by_filters(
        self,
        *,
        machine_id: int | None = None,
        line_code: str | None = None,
        product_code: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ProductionRecord]:
        """
        根据多个可选条件组合查询生产记录。

        以后 GET /production-records
        会主要使用这个方法。
        """

        stmt = select(ProductionRecord)

        if machine_id is not None:
            stmt = stmt.where(
                ProductionRecord.machine_id == machine_id
            )

        if line_code is not None:
            stmt = stmt.where(
                ProductionRecord.line_code == line_code
            )

        if product_code is not None:
            stmt = stmt.where(
                ProductionRecord.product_code
                == product_code
            )

        if start_date is not None:
            stmt = stmt.where(
                ProductionRecord.production_date
                >= start_date
            )

        if end_date is not None:
            stmt = stmt.where(
                ProductionRecord.production_date
                <= end_date
            )

        stmt = stmt.order_by(
            ProductionRecord.production_date.desc(),
            ProductionRecord.id.desc(),
        )

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def create(
        self,
        *,
        machine_id: int,
        line_code: str,
        product_code: str,
        planned_qty: int,
        actual_qty: int,
        defect_qty: int,
        production_date: date,
    ) -> ProductionRecord:
        """
        创建生产记录
        """

        record = ProductionRecord(
            machine_id=machine_id,
            line_code=line_code,
            product_code=product_code,
            planned_qty=planned_qty,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
            production_date=production_date,
        )

        self.db.add(record)

        self.db.flush()
        self.db.refresh(record)

        return record

    def update(
        self,
        record: ProductionRecord,
        **data,
    ) -> ProductionRecord:
        """
        更新生产记录
        """

        allowed_fields = {
            "machine_id",
            "line_code",
            "product_code",
            "planned_qty",
            "actual_qty",
            "defect_qty",
            "production_date",
        }

        for field, value in data.items():
            if field in allowed_fields:
                setattr(record, field, value)

        self.db.flush()
        self.db.refresh(record)

        return record

    def delete(
        self,
        record: ProductionRecord,
    ) -> None:
        """
        删除生产记录。

        V0 可用于学习 CRUD。
        后续真实业务中生产历史一般不建议物理删除。
        """

        self.db.delete(record)
        self.db.flush()