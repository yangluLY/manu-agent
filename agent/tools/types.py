from typing import Any

from pydantic import BaseModel


class ToolError(BaseModel):
    """
    Tool 执行失败时返回的结构化错误。
    不暴露数据库异常、堆栈等内部实现信息。
    """

    code: str
    message: str
    details: dict[str, Any] | None = None


class ToolResult(BaseModel):
    """
    ManuAgent 所有 Tool 的统一返回结构。
    """

    success: bool
    data: Any | None = None
    error: ToolError | None = None

    @classmethod
    def ok(cls, data: Any) -> "ToolResult":
        return cls(
            success=True,
            data=data,
            error=None,
        )

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> "ToolResult":
        return cls(
            success=False,
            data=None,
            error=ToolError(
                code=code,
                message=message,
                details=details,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
