import logging
from typing import Any

from agent.registry import ToolRegistry
from agent.tools.types import ToolResult

logger = logging.getLogger(__name__)


class ToolExecutor:

    def __init__(
        self,
        registry: ToolRegistry,
    ):
        self.registry = registry

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:

        handler = self.registry.get_handler(tool_name)

        if handler is None:
            return ToolResult.fail(
                code="TOOL_NOT_FOUND",
                message="Tool not found",
                details={
                    "tool_name": tool_name,
                },
            )

        try:
            return handler(**arguments)

        except TypeError:
            logger.exception(
                "Invalid arguments for tool: %s",
                tool_name,
            )

            return ToolResult.fail(
                code="INVALID_TOOL_ARGUMENTS",
                message="Invalid tool arguments",
            )

        except Exception:
            logger.exception(
                "Tool execution failed: %s",
                tool_name,
            )

            return ToolResult.fail(
                code="TOOL_EXECUTION_ERROR",
                message="Tool execution failed",
            )