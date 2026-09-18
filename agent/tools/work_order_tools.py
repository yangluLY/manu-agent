from typing import Any, ClassVar

from apps.api.app.core.exceptions import MachineNotFoundException
from agent.tools.serializers import serialize_machine, serialize_work_order
from agent.tools.types import ToolResult
from services.mes.machine_service import MachineService
from services.mes.work_order_service import WorkOrderService


class WorkOrderTools:
    """Work-order query and creation tools."""

    ALLOWED_TYPES: ClassVar[set[str]] = {
        "maintenance",
        "repair",
        "inspection",
    }
    ALLOWED_PRIORITIES: ClassVar[set[str]] = {
        "low",
        "medium",
        "high",
        "urgent",
    }

    def __init__(
        self,
        work_order_service: WorkOrderService,
        machine_service: MachineService,
    ):
        self.work_order_service = work_order_service
        self.machine_service = machine_service

    def get_machine_work_orders(
        self,
        machine_code: str,
        open_only: bool = False,
    ) -> ToolResult:
        machine_or_error = self._get_machine(machine_code)
        if isinstance(machine_or_error, ToolResult):
            return machine_or_error
        machine = machine_or_error

        if open_only:
            work_orders = self.work_order_service.get_open_machine_work_orders(
                machine.id
            )
        else:
            work_orders = self.work_order_service.get_machine_work_orders(machine.id)

        return ToolResult.ok(
            {
                "machine": serialize_machine(machine),
                "open_only": open_only,
                "count": len(work_orders),
                "work_orders": [
                    serialize_work_order(item, machine_code=machine.code)
                    for item in work_orders
                ],
            }
        )

    def create_work_order(
        self,
        machine_code: str,
        type: str,
        priority: str,
        description: str,
        assigned_to: str | None = None,
    ) -> ToolResult:
        normalized_type = type.strip().lower()
        normalized_priority = priority.strip().lower()
        normalized_description = description.strip()

        if normalized_type not in self.ALLOWED_TYPES:
            return ToolResult.fail(
                code="INVALID_WORK_ORDER_TYPE",
                message="Invalid work order type",
                details={"allowed_values": sorted(self.ALLOWED_TYPES)},
            )
        if normalized_priority not in self.ALLOWED_PRIORITIES:
            return ToolResult.fail(
                code="INVALID_WORK_ORDER_PRIORITY",
                message="Invalid work order priority",
                details={"allowed_values": sorted(self.ALLOWED_PRIORITIES)},
            )
        if not normalized_description:
            return ToolResult.fail(
                code="INVALID_WORK_ORDER_DESCRIPTION",
                message="Work order description cannot be empty",
            )

        machine_or_error = self._get_machine(machine_code)
        if isinstance(machine_or_error, ToolResult):
            return machine_or_error
        machine = machine_or_error

        work_order = self.work_order_service.create_work_order(
            machine_id=machine.id,
            type=normalized_type,
            priority=normalized_priority,
            description=normalized_description,
            assigned_to=(assigned_to.strip() or None) if assigned_to else None,
        )

        return ToolResult.ok(
            serialize_work_order(work_order, machine_code=machine.code)
        )

    def _get_machine(self, machine_code: str) -> Any | ToolResult:
        normalized_code = machine_code.strip().upper()
        try:
            return self.machine_service.get_machine_by_code(normalized_code)
        except MachineNotFoundException:
            return ToolResult.fail(
                code="MACHINE_NOT_FOUND",
                message="Machine not found",
                details={"machine_code": normalized_code},
            )
