from typing import Any, ClassVar

from sqlalchemy.orm import Session

from apps.api.app.core.exceptions import (
    InvalidMachineStatusException,
    MachineCodeExistsException,
    MachineNotFoundException,
)
from services.database.models.machine import Machine
from services.database.repositories.machine_repository import MachineRepository


class MachineService:
    ALLOWED_STATUSES: ClassVar[set[str]] = {
        "running",
        "idle",
        "alarm",
        "maintenance",
        "offline",
    }

    def __init__(self, db: Session):
        self.repository = MachineRepository(db)

    def get_machines(self) -> list[Machine]:
        """
        获取所有设备
        """
        return self.repository.find_all()

    def get_machine(self, machine_id: int) -> Machine:
        """
        根据 ID 获取设备
        """
        machine = self.repository.find_by_id(machine_id)

        if machine is None:
            raise MachineNotFoundException(
                f"Machine with id={machine_id} not found"
            )

        return machine

    def get_machine_by_code(self, code: str) -> Machine:
        """
        根据设备编码获取设备
        """
        machine = self.repository.find_by_code(code)

        if machine is None:
            raise MachineNotFoundException(
                f"Machine with code={code} not found"
            )

        return machine

    def create_machine(
        self,
        data: dict[str, Any],
    ) -> Machine:
        """
        创建设备
        """

        code = data["code"]

        existing_machine = self.repository.find_by_code(code)

        if existing_machine is not None:
            raise MachineCodeExistsException(
                f"Machine with code={code} already exists"
            )

        status = data.get("status", "offline")

        self._validate_status(status)

        return self.repository.create(data)

    def update_machine(
        self,
        machine_id: int,
        data: dict[str, Any],
    ) -> Machine:
        """
        更新设备
        """

        machine = self.get_machine(machine_id)

        if "status" in data:
            self._validate_status(data["status"])

        return self.repository.update(
            machine,
            data,
        )

    def delete_machine(
        self,
        machine_id: int,
    ) -> None:
        """
        删除设备
        """

        machine = self.get_machine(machine_id)

        self.repository.delete(machine)

    def _validate_status(self, status: str) -> None:
        """
        校验设备状态
        """

        if status not in self.ALLOWED_STATUSES:
            raise InvalidMachineStatusException(
                f"Invalid machine status: {status}"
            )
