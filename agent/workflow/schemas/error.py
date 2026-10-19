
from typing import Literal

from pydantic import BaseModel, Field

WorkflowErrorCode = Literal[
    "TIMEOUT",
    "CONNECTION_ERROR",
    "SQL_VALIDATION_ERROR",
    "PERMISSION_DENIED",
    "INVALID_INPUT",
    "EXECUTION_ERROR",
]


class WorkflowError(BaseModel):
    """对外安全展示的执行错误。"""

    code: WorkflowErrorCode
    message: str

    retryable: bool = False
    attempts: int = Field(default=1, ge=1)
