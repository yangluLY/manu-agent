from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.database.models.machine import Machine


class MachineRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[Machine]:
        """
        查询所有设备
        """
        stmt = select(Machine).order_by(Machine.id)

        result = self.db.execute(stmt)

        return list(result.scalars().all())

    def find_by_id(self, machine_id: int) -> Machine | None:
        """
        根据数据库主键 ID 查询设备
        """
        return self.db.get(Machine, machine_id)

    def find_by_code(self, code: str) -> Machine | None:
        """
        根据设备编码查询设备
        """
        stmt = select(Machine).where(Machine.code == code)

        result = self.db.execute(stmt)

        return result.scalar_one_or_none()

    def create(self, data: dict[str, Any]) -> Machine:
        """
        创建设备
        """
        machine = Machine(**data)

        self.db.add(machine)

        try:
            self.db.commit()
            self.db.refresh(machine)
        except Exception:
            self.db.rollback()
            raise

        return machine

    def update(
        self,
        machine: Machine,
        data: dict[str, Any],
    ) -> Machine:
        """
        更新设备
        """
        for field, value in data.items():
            setattr(machine, field, value)

        try:
            self.db.commit()
            self.db.refresh(machine)
        except Exception:
            self.db.rollback()
            raise

        return machine

    def delete(self, machine: Machine) -> None:
        """
        删除设备
        """
        self.db.delete(machine)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise