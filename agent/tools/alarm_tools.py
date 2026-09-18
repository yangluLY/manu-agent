from agent.tools.serializers import serialize_alarm, serialize_machine
from agent.tools.types import ToolResult
from apps.api.app.core.exceptions import MachineNotFoundException
from services.mes.alarm_service import AlarmService
from services.mes.machine_service import MachineService


class AlarmTools:
    """Read-only alarm tools exposed to the manufacturing agent."""

    def __init__(
        self,
        alarm_service: AlarmService,
        machine_service: MachineService,
    ):
        self.alarm_service = alarm_service
        self.machine_service = machine_service

    def get_machine_alarms(
        self,
        machine_code: str,
        active_only: bool = False,
    ) -> ToolResult:
        normalized_code = machine_code.strip().upper()

        try:
            machine = self.machine_service.get_machine_by_code(normalized_code)
        except MachineNotFoundException:
            return ToolResult.fail(
                code="MACHINE_NOT_FOUND",
                message="Machine not found",
                details={"machine_code": normalized_code},
            )

        if active_only:
            alarms = self.alarm_service.get_active_machine_alarms(machine.id)
        else:
            alarms = self.alarm_service.get_machine_alarms(machine.id)

        return ToolResult.ok(
            {
                "machine": serialize_machine(machine),
                "active_only": active_only,
                "count": len(alarms),
                "alarms": [
                    serialize_alarm(alarm, machine_code=machine.code)
                    for alarm in alarms
                ],
            }
        )
