from sqlalchemy import select
from sqlalchemy.orm import Session

from services.database.models.work_order import WorkOrder


class WorkOrderRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[WorkOrder]:
        """
        查询全部工单
        """
        stmt = (
            select(WorkOrder)
            .order_by(WorkOrder.created_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def find_by_id(
        self,
        work_order_id: int,
    ) -> WorkOrder | None:
        """
        根据数据库 ID 查询工单
        """
        stmt = (
            select(WorkOrder)
            .where(WorkOrder.id == work_order_id)
        )

        return self.db.scalar(stmt)

    def find_by_order_no(
        self,
        order_no: str,
    ) -> WorkOrder | None:
        """
        根据业务工单编号查询

        例如：
        WO-20260915-001
        """
        stmt = (
            select(WorkOrder)
            .where(WorkOrder.order_no == order_no)
        )

        return self.db.scalar(stmt)

    def find_by_machine_id(
        self,
        machine_id: int,
    ) -> list[WorkOrder]:
        """
        查询某台设备的全部工单
        """
        stmt = (
            select(WorkOrder)
            .where(WorkOrder.machine_id == machine_id)
            .order_by(WorkOrder.created_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def find_by_status(
        self,
        status: str,
    ) -> list[WorkOrder]:
        """
        根据状态查询工单

        pending
        in_progress
        completed
        cancelled
        """
        stmt = (
            select(WorkOrder)
            .where(WorkOrder.status == status)
            .order_by(WorkOrder.created_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def find_open_by_machine_id(
        self,
        machine_id: int,
    ) -> list[WorkOrder]:
        """
        查询设备当前未完成的工单
        """
        stmt = (
            select(WorkOrder)
            .where(
                WorkOrder.machine_id == machine_id,
                WorkOrder.status.in_(
                    ["pending", "in_progress"]
                ),
            )
            .order_by(WorkOrder.created_at.desc())
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def create(
        self,
        *,
        order_no: str,
        machine_id: int,
        type: str,
        priority: str,
        description: str,
        assigned_to: str | None = None,
        status: str = "pending",
    ) -> WorkOrder:
        """
        创建维修工单
        """

        work_order = WorkOrder(
            order_no=order_no,
            machine_id=machine_id,
            type=type,
            priority=priority,
            description=description,
            status=status,
            assigned_to=assigned_to,
        )

        self.db.add(work_order)

        self.db.flush()
        self.db.refresh(work_order)

        return work_order

    def update(
        self,
        work_order: WorkOrder,
        **data,
    ) -> WorkOrder:
        """
        更新工单
        """

        allowed_fields = {
            "type",
            "priority",
            "description",
            "status",
            "assigned_to",
        }

        for field, value in data.items():
            if field in allowed_fields:
                setattr(work_order, field, value)

        self.db.flush()
        self.db.refresh(work_order)

        return work_order

    def delete(
        self,
        work_order: WorkOrder,
    ) -> None:
        """
        删除工单

        V0 学习阶段可以使用。
        企业项目通常更倾向于取消工单，
        而不是物理删除。
        """
        self.db.delete(work_order)
        self.db.flush()