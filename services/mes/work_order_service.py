from datetime import datetime

from sqlalchemy.orm import Session

from apps.api.app.core.exceptions import (
    CompletedWorkOrderCancellationException,
    MachineNotFoundException,
    WorkOrderAlreadyCompletedException,
    WorkOrderNotFoundException,
)
from services.database.models.work_order import WorkOrder
from services.database.repositories.machine_repository import MachineRepository
from services.database.repositories.work_order_repository import (
    WorkOrderRepository,
)


class WorkOrderService:

    def __init__(self, db: Session):
        self.db = db
        self.work_order_repo = WorkOrderRepository(db)
        self.machine_repo = MachineRepository(db)

    def get_all_work_orders(self) -> list[WorkOrder]:
        """
        查询全部工单
        """
        return self.work_order_repo.find_all()

    def get_work_order(
        self,
        work_order_id: int,
    ) -> WorkOrder:
        """
        根据 ID 查询工单
        """

        work_order = self.work_order_repo.find_by_id(work_order_id)

        if work_order is None:
            raise WorkOrderNotFoundException()

        return work_order

    def get_work_order_by_no(
        self,
        order_no: str,
    ) -> WorkOrder:
        """
        根据工单编号查询
        """

        work_order = self.work_order_repo.find_by_order_no(order_no)

        if work_order is None:
            raise WorkOrderNotFoundException()

        return work_order

    def get_machine_work_orders(
        self,
        machine_id: int,
    ) -> list[WorkOrder]:
        """
        查询某台设备的全部工单
        """

        machine = self.machine_repo.find_by_id(machine_id)

        if machine is None:
            raise MachineNotFoundException()

        return self.work_order_repo.find_by_machine_id(machine_id)

    def get_open_machine_work_orders(
        self,
        machine_id: int,
    ) -> list[WorkOrder]:
        """
        查询设备当前未完成工单
        """

        machine = self.machine_repo.find_by_id(machine_id)

        if machine is None:
            raise MachineNotFoundException()

        return self.work_order_repo.find_open_by_machine_id(machine_id)

    def create_work_order(
        self,
        *,
        machine_id: int,
        type: str,
        priority: str,
        description: str,
        assigned_to: str | None = None,
    ) -> WorkOrder:
        """
        创建工单
        """

        machine = self.machine_repo.find_by_id(machine_id)

        if machine is None:
            raise MachineNotFoundException()

        order_no = self._generate_order_no()

        try:
            work_order = self.work_order_repo.create(
                order_no=order_no,
                machine_id=machine_id,
                type=type,
                priority=priority,
                description=description,
                assigned_to=assigned_to,
                status="pending",
            )

            self.db.commit()
            self.db.refresh(work_order)

            return work_order

        except Exception:
            self.db.rollback()
            raise

    def update_work_order(
        self,
        work_order_id: int,
        **data,
    ) -> WorkOrder:
        """
        更新工单
        """

        work_order = self.work_order_repo.find_by_id(work_order_id)

        if work_order is None:
            raise WorkOrderNotFoundException()

        try:
            work_order = self.work_order_repo.update(
                work_order,
                **data,
            )

            self.db.commit()
            self.db.refresh(work_order)

            return work_order

        except Exception:
            self.db.rollback()
            raise

    def complete_work_order(
        self,
        work_order_id: int,
    ) -> WorkOrder:
        """
        完成工单
        """

        work_order = self.work_order_repo.find_by_id(work_order_id)

        if work_order is None:
            raise WorkOrderNotFoundException()

        if work_order.status == "completed":
            raise WorkOrderAlreadyCompletedException()

        try:
            work_order = self.work_order_repo.update(
                work_order,
                status="completed",
            )

            self.db.commit()
            self.db.refresh(work_order)

            return work_order

        except Exception:
            self.db.rollback()
            raise

    def cancel_work_order(
        self,
        work_order_id: int,
    ) -> WorkOrder:
        """
        取消工单
        """

        work_order = self.work_order_repo.find_by_id(work_order_id)

        if work_order is None:
            raise WorkOrderNotFoundException()

        if work_order.status == "completed":
            raise CompletedWorkOrderCancellationException()

        try:
            work_order = self.work_order_repo.update(
                work_order,
                status="cancelled",
            )

            self.db.commit()
            self.db.refresh(work_order)

            return work_order

        except Exception:
            self.db.rollback()
            raise

    def _generate_order_no(self) -> str:
        """
        生成简单工单编号

        示例：
        WO-20260915-153045
        """

        now = datetime.now()  # noqa: DTZ005

        return now.strftime("WO-%Y%m%d-%H%M%S")
