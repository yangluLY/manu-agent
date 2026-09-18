from agent.tools.serializers import serialize_machine, to_json_value
from agent.tools.types import ToolResult
from apps.api.app.core.exceptions import MachineNotFoundException
from services.mes.machine_service import MachineService


class MachineTools:
    """Provider-independent tools backed by ``MachineService``."""

    def __init__(self, machine_service: MachineService):
        self.machine_service = machine_service

    def get_machine_by_code(
        self,
        machine_code: str,
    ) -> ToolResult:
        """Backward-compatible alias for ``get_machine_detail``."""
        return self.get_machine_detail(machine_code)

    def get_machine_detail(
        self,
        machine_code: str,
    ) -> ToolResult:
        normalized_code = machine_code.strip().upper()
        if not normalized_code:
            return ToolResult.fail(
                code="INVALID_MACHINE_CODE",
                message="Machine code cannot be empty",
            )

        try:
            machine = self.machine_service.get_machine_by_code(normalized_code)
        except MachineNotFoundException:
            return ToolResult.fail(
                code="MACHINE_NOT_FOUND",
                message="Machine not found",
                details={"machine_code": normalized_code},
            )

        return ToolResult.ok(serialize_machine(machine))

    def get_machine_status(
        self,
        machine_code: str,
    ) -> ToolResult:
        detail = self.get_machine_detail(machine_code)
        if not detail.success:
            return detail

        return ToolResult.ok(
            {
                "code": detail.data["code"],
                "status": detail.data["status"],
                "last_heartbeat_at": detail.data["last_heartbeat_at"],
            }
        )

    def list_machines(
        self,
        line_code: str | None = None,
        status: str | None = None,
    ) -> ToolResult:
        machines = self.machine_service.get_machines()
        normalized_line = line_code.strip().upper() if line_code else None
        normalized_status = status.strip().lower() if status else None

        filtered = [
            machine
            for machine in machines
            if (
                normalized_line is None
                or machine.line_code == normalized_line
            )
            and (
                normalized_status is None
                or to_json_value(machine.status) == normalized_status
            )
        ]

        return ToolResult.ok(
            {
                "count": len(filtered),
                "machines": [serialize_machine(machine) for machine in filtered],
            }
        )
