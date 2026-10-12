from datetime import date

from agent.tools.serializers import serialize_machine
from agent.tools.types import ToolResult
from apps.api.app.core.exceptions import (
    InvalidDateRangeException,
    MachineNotFoundException,
)
from services.mes.machine_service import MachineService
from services.mes.production_service import ProductionService


class ProductionTools:
    """Production KPI tools backed by ``ProductionService``."""

    def __init__(
        self,
        production_service: ProductionService,
        machine_service: MachineService,
    ):
        self.production_service = production_service
        self.machine_service = machine_service

    def get_machine_production_stats(
        self,
        machine_code: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ToolResult:
        parsed_start = self._parse_date(start_date, "start_date")
        if isinstance(parsed_start, ToolResult):
            return parsed_start

        parsed_end = self._parse_date(end_date, "end_date")
        if isinstance(parsed_end, ToolResult):
            return parsed_end

        if parsed_start and parsed_end and parsed_start > parsed_end:
            return ToolResult.fail(
                code="INVALID_DATE_RANGE",
                message="start_date cannot be later than end_date",
                details={"start_date": start_date, "end_date": end_date},
            )

        normalized_code = machine_code.strip().upper()
        try:
            machine = self.machine_service.get_machine_by_code(normalized_code)
            summary = self.production_service.get_summary(
                machine_id=machine.id,
                start_date=parsed_start,
                end_date=parsed_end,
            )
        except MachineNotFoundException:
            return ToolResult.fail(
                code="MACHINE_NOT_FOUND",
                message="Machine not found",
                details={"machine_code": normalized_code},
            )
        except InvalidDateRangeException:
            return ToolResult.fail(
                code="INVALID_DATE_RANGE",
                message="start_date cannot be later than end_date",
                details={"start_date": start_date, "end_date": end_date},
            )

        return ToolResult.ok(
            {
                "machine": serialize_machine(machine),
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "summary": summary,
            }
        )

    @staticmethod
    def _parse_date(
        value: str | None,
        field_name: str,
    ) -> date | None | ToolResult:
        if value is None:
            return None

        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return ToolResult.fail(
                code="INVALID_DATE_FORMAT",
                message=f"{field_name} must use YYYY-MM-DD format",
                details={field_name: value},
            )
