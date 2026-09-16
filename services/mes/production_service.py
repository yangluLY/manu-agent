from datetime import date

from sqlalchemy.orm import Session

from apps.api.app.core.exceptions import (
    InvalidDateRangeException,
    InvalidProductionQuantityException,
    MachineNotFoundException,
    ProductionRecordNotFoundException,
)
from services.database.models.production_record import ProductionRecord
from services.database.repositories.machine_repository import MachineRepository
from services.database.repositories.production_repository import (
    ProductionRepository,
)


class ProductionService:

    def __init__(self, db: Session):
        self.db = db

        self.production_repo = ProductionRepository(db)
        self.machine_repo = MachineRepository(db)

    def get_all_records(
        self,
    ) -> list[ProductionRecord]:
        """
        查询全部生产记录
        """
        return self.production_repo.find_all()

    def get_record(
        self,
        record_id: int,
    ) -> ProductionRecord:
        """
        根据 ID 查询生产记录
        """

        record = self.production_repo.find_by_id(record_id)

        if record is None:
            raise ProductionRecordNotFoundException()

        return record

    def get_records(
        self,
        *,
        machine_id: int | None = None,
        line_code: str | None = None,
        product_code: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ProductionRecord]:
        """
        根据条件查询生产记录
        """

        if machine_id is not None:
            machine = self.machine_repo.find_by_id(
                machine_id
            )

            if machine is None:
                raise MachineNotFoundException()

        if (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            raise InvalidDateRangeException()

        return self.production_repo.find_by_filters(
            machine_id=machine_id,
            line_code=line_code,
            product_code=product_code,
            start_date=start_date,
            end_date=end_date,
        )

    def create_record(
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

        # 设备必须真实存在
        machine = self.machine_repo.find_by_id(
            machine_id
        )

        if machine is None:
            raise MachineNotFoundException()

        self._validate_quantities(
            planned_qty=planned_qty,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
        )

        try:
            record = self.production_repo.create(
                machine_id=machine_id,
                line_code=line_code,
                product_code=product_code,
                planned_qty=planned_qty,
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                production_date=production_date,
            )

            self.db.commit()
            self.db.refresh(record)

            return record

        except Exception:
            self.db.rollback()
            raise

    def update_record(
        self,
        record_id: int,
        **data,
    ) -> ProductionRecord:
        """
        修改生产记录
        """

        record = self.production_repo.find_by_id(
            record_id
        )

        if record is None:
            raise ProductionRecordNotFoundException()

        # 如果修改 machine_id，需要确认设备存在
        if "machine_id" in data:
            machine_id = data["machine_id"]

            machine = self.machine_repo.find_by_id(
                machine_id
            )

            if machine is None:
                raise MachineNotFoundException()

        # 使用修改后的值进行整体校验
        planned_qty = data.get(
            "planned_qty",
            record.planned_qty,
        )

        actual_qty = data.get(
            "actual_qty",
            record.actual_qty,
        )

        defect_qty = data.get(
            "defect_qty",
            record.defect_qty,
        )

        self._validate_quantities(
            planned_qty=planned_qty,
            actual_qty=actual_qty,
            defect_qty=defect_qty,
        )

        try:
            record = self.production_repo.update(
                record,
                **data,
            )

            self.db.commit()
            self.db.refresh(record)

            return record

        except Exception:
            self.db.rollback()
            raise

    def get_record_metrics(
        self,
        record_id: int,
    ) -> dict:
        """
        获取单条生产记录的 KPI
        """

        record = self.get_record(record_id)

        completion_rate = self._calculate_completion_rate(
            planned_qty=record.planned_qty,
            actual_qty=record.actual_qty,
        )

        defect_rate = self._calculate_defect_rate(
            actual_qty=record.actual_qty,
            defect_qty=record.defect_qty,
        )

        return {
            "record_id": record.id,
            "machine_id": record.machine_id,
            "line_code": record.line_code,
            "product_code": record.product_code,
            "production_date": record.production_date,
            "planned_qty": record.planned_qty,
            "actual_qty": record.actual_qty,
            "defect_qty": record.defect_qty,
            "completion_rate": completion_rate,
            "defect_rate": defect_rate,
        }

    def get_summary(
        self,
        *,
        machine_id: int | None = None,
        line_code: str | None = None,
        product_code: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        汇总生产数据。

        后面 BI Agent / SQL Agent 会大量使用类似能力。
        """

        records = self.get_records(
            machine_id=machine_id,
            line_code=line_code,
            product_code=product_code,
            start_date=start_date,
            end_date=end_date,
        )

        total_planned_qty = sum(
            record.planned_qty
            for record in records
        )

        total_actual_qty = sum(
            record.actual_qty
            for record in records
        )

        total_defect_qty = sum(
            record.defect_qty
            for record in records
        )

        completion_rate = self._calculate_completion_rate(
            planned_qty=total_planned_qty,
            actual_qty=total_actual_qty,
        )

        defect_rate = self._calculate_defect_rate(
            actual_qty=total_actual_qty,
            defect_qty=total_defect_qty,
        )

        return {
            "record_count": len(records),
            "planned_qty": total_planned_qty,
            "actual_qty": total_actual_qty,
            "defect_qty": total_defect_qty,
            "completion_rate": completion_rate,
            "defect_rate": defect_rate,
        }

    @staticmethod
    def _validate_quantities(
        *,
        planned_qty: int,
        actual_qty: int,
        defect_qty: int,
    ) -> None:
        """
        校验生产数量
        """

        if planned_qty < 0:
            raise InvalidProductionQuantityException(
                "Planned quantity cannot be negative"
            )

        if actual_qty < 0:
            raise InvalidProductionQuantityException(
                "Actual quantity cannot be negative"
            )

        if defect_qty < 0:
            raise InvalidProductionQuantityException(
                "Defect quantity cannot be negative"
            )

        if defect_qty > actual_qty:
            raise InvalidProductionQuantityException(
                "Defect quantity cannot exceed actual quantity"
            )

    @staticmethod
    def _calculate_completion_rate(
        *,
        planned_qty: int,
        actual_qty: int,
    ) -> float:
        """
        生产完成率：

        actual_qty / planned_qty * 100
        """

        if planned_qty == 0:
            return 0.0

        return round(
            actual_qty / planned_qty * 100,
            2,
        )

    @staticmethod
    def _calculate_defect_rate(
        *,
        actual_qty: int,
        defect_qty: int,
    ) -> float:
        """
        不良率：

        defect_qty / actual_qty * 100
        """

        if actual_qty == 0:
            return 0.0

        return round(
            defect_qty / actual_qty * 100,
            2,
        )
