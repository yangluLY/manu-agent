class AppException(Exception):
    """
    项目基础业务异常。
    """

    status_code = 500
    detail = "Internal server error"

    def __init__(
        self,
        detail: str | None = None,
    ):
        if detail is not None:
            self.detail = detail

        super().__init__(self.detail)


class NotFoundException(AppException):
    status_code = 404
    detail = "Resource not found"


class ConflictException(AppException):
    status_code = 409
    detail = "Resource conflict"


class BadRequestException(AppException):
    status_code = 400
    detail = "Bad request"


class ServiceUnavailableException(AppException):
    status_code = 503
    detail = "Service unavailable"


class MachineNotFoundException(
    NotFoundException
):
    detail = "Machine not found"


class MachineCodeExistsException(
    ConflictException
):
    detail = "Machine code already exists"


class InvalidMachineStatusException(
    BadRequestException
):
    detail = "Invalid machine status"


class MaterialNotFoundException(
    NotFoundException
):
    detail = "Material not found"


class MaterialCodeExistsException(
    ConflictException
):
    detail = "Material code already exists"


class InvalidInventoryQuantityException(
    BadRequestException
):
    detail = "Invalid inventory quantity"


class InsufficientInventoryException(
    ConflictException
):
    detail = "Insufficient inventory"


class AlarmNotFoundException(
    NotFoundException
):
    detail = "Alarm not found"


class AlarmAlreadyResolvedException(
    ConflictException
):
    detail = "Alarm already resolved"


class WorkOrderNotFoundException(
    NotFoundException
):
    detail = "Work order not found"


class WorkOrderAlreadyCompletedException(
    ConflictException
):
    detail = "Work order already completed"


class CompletedWorkOrderCancellationException(
    ConflictException
):
    detail = "Completed work order cannot be cancelled"


class ProductionRecordNotFoundException(
    NotFoundException
):
    detail = "Production record not found"


class InvalidDateRangeException(
    BadRequestException
):
    detail = "Start date cannot be later than end date"


class InvalidProductionQuantityException(
    BadRequestException
):
    detail = "Invalid production quantity"


class DatabaseUnavailableException(
    ServiceUnavailableException
):
    detail = "Database connection failed"
