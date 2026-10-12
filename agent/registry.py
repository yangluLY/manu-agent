from collections.abc import Callable
from typing import Any

from agent.tools.alarm_tools import AlarmTools
from agent.tools.inventory_tools import InventoryTools
from agent.tools.machine_tools import MachineTools
from agent.tools.production_tools import ProductionTools
from agent.tools.types import ToolResult
from agent.tools.work_order_tools import WorkOrderTools
from agent.tools.knowledge_tools import KnowledgeTools

ToolHandler = Callable[..., ToolResult]
ToolSchema = dict[str, Any]


class ToolRegistry:
    """保存提供给大模型的 Tool Schema 及其 Python 处理方法。"""

    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}
        self._schemas: list[ToolSchema] = []

    def register(
        self,
        *,
        name: str,
        handler: ToolHandler,
        schema: ToolSchema,
    ) -> None:
        if name in self._handlers:
            raise ValueError(f"Tool already registered: {name}")
        if schema.get("type") != "function":
            raise ValueError(f"Tool schema type must be function: {name}")
        if schema.get("name") != name:
            raise ValueError(f"Tool schema name does not match handler: {name}")

        self._handlers[name] = handler
        self._schemas.append(schema)

    @property
    def schemas(self) -> list[ToolSchema]:
        """返回供 Responses API 使用的 Tool Schema 副本。"""
        return list(self._schemas)

    def get_handler(self, name: str) -> ToolHandler | None:
        return self._handlers.get(name)

    def has_tool(self, name: str) -> bool:
        return name in self._handlers

    @property
    def tool_names(self) -> list[str]:
        return list(self._handlers)


def _function_schema(
    *,
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str],
) -> ToolSchema:
    """创建 DeepSeek Responses API 使用的函数工具 Schema。"""
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


def build_tool_registry(
    machine_tools: MachineTools,
    alarm_tools: AlarmTools,
    inventory_tools: InventoryTools,
    work_order_tools: WorkOrderTools,
    production_tools: ProductionTools,
    knowledge_tools: KnowledgeTools,
) -> ToolRegistry:
    """注册 ManuAgent 可供大模型调用的 MES 与知识库工具。"""
    registry = ToolRegistry()

    registry.register(
        name="list_machines",
        handler=machine_tools.list_machines,
        schema=_function_schema(
            name="list_machines",
            description="查询设备列表，可按产线编码或运行状态筛选。",
            properties={
                "line_code": {
                    "type": "string",
                    "description": "可选产线编码，例如 LINE-A。",
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "running",
                        "idle",
                        "alarm",
                        "maintenance",
                        "offline",
                    ],
                    "description": "可选设备运行状态。",
                },
            },
            required=[],
        ),
    )

    registry.register(
        name="get_machine_by_code",
        handler=machine_tools.get_machine_by_code,
        schema=_function_schema(
            name="get_machine_by_code",
            description="根据设备编码查询设备基础信息。",
            properties={
                "machine_code": {
                    "type": "string",
                    "description": "设备编码，例如 MC-003。",
                },
            },
            required=["machine_code"],
        ),
    )

    registry.register(
        name="get_machine_detail",
        handler=machine_tools.get_machine_detail,
        schema=_function_schema(
            name="get_machine_detail",
            description="根据设备编码查询设备详情和当前状态。",
            properties={
                "machine_code": {
                    "type": "string",
                    "description": "设备编码，例如 MC-003。",
                },
            },
            required=["machine_code"],
        ),
    )

    registry.register(
        name="get_machine_status",
        handler=machine_tools.get_machine_status,
        schema=_function_schema(
            name="get_machine_status",
            description="根据设备编码查询当前运行状态和最后心跳时间。",
            properties={
                "machine_code": {
                    "type": "string",
                    "description": "设备编码，例如 MC-003。",
                },
            },
            required=["machine_code"],
        ),
    )

    registry.register(
        name="get_machine_alarms",
        handler=alarm_tools.get_machine_alarms,
        schema=_function_schema(
            name="get_machine_alarms",
            description="查询指定设备的报警，可选择只查看未恢复报警。",
            properties={
                "machine_code": {
                    "type": "string",
                    "description": "设备编码，例如 MC-003。",
                },
                "active_only": {
                    "type": "boolean",
                    "description": "为 true 时只返回尚未恢复的报警。",
                    "default": False,
                },
            },
            required=["machine_code"],
        ),
    )

    registry.register(
        name="get_machine_production_stats",
        handler=production_tools.get_machine_production_stats,
        schema=_function_schema(
            name="get_machine_production_stats",
            description=(
                "查询指定设备在日期范围内的计划产量、实际产量、"
                "不良品数、完成率和不良率。"
            ),
            properties={
                "machine_code": {
                    "type": "string",
                    "description": "设备编码，例如 MC-003。",
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "可选开始日期，格式 YYYY-MM-DD。",
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "可选结束日期，格式 YYYY-MM-DD。",
                },
            },
            required=["machine_code"],
        ),
    )

    registry.register(
        name="get_low_stock_materials",
        handler=inventory_tools.get_low_stock_materials,
        schema=_function_schema(
            name="get_low_stock_materials",
            description="查询当前库存量低于安全库存量的物料。",
            properties={},
            required=[],
        ),
    )

    registry.register(
        name="get_machine_work_orders",
        handler=work_order_tools.get_machine_work_orders,
        schema=_function_schema(
            name="get_machine_work_orders",
            description="查询指定设备的维修、保养和巡检工单。",
            properties={
                "machine_code": {
                    "type": "string",
                    "description": "设备编码，例如 MC-003。",
                },
                "open_only": {
                    "type": "boolean",
                    "description": "为 true 时只返回待处理或处理中的工单。",
                    "default": False,
                },
            },
            required=["machine_code"],
        ),
    )

    registry.register(
        name="create_work_order",
        handler=work_order_tools.create_work_order,
        schema=_function_schema(
            name="create_work_order",
            description="为指定设备创建维修、保养或巡检工单。",
            properties={
                "machine_code": {
                    "type": "string",
                    "description": "设备编码，例如 MC-003。",
                },
                "type": {
                    "type": "string",
                    "enum": ["maintenance", "repair", "inspection"],
                    "description": "工单类型。",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "工单优先级。",
                },
                "description": {
                    "type": "string",
                    "description": "需要处理的问题和维修要求。",
                },
                "assigned_to": {
                    "type": "string",
                    "description": "可选负责人姓名。",
                },
            },
            required=[
                "machine_code",
                "type",
                "priority",
                "description",
            ],
        ),
    )

    registry.register(
        name="search_knowledge",
        handler=knowledge_tools.search_knowledge,
        schema=_function_schema(
            name="search_knowledge",
            description=(
                "搜索 ManuAgent 企业知识库。"
                "适用于查询设备说明书、设备故障原因、"
                "报警处理方法、维修 SOP、操作规范、"
                "生产 SOP 和质量规范等企业知识。"
            ),
            properties={
                "query": {
                    "type": "string",
                    "description": (
                        "需要检索的知识问题。"
                        "应包含明确的设备、报警代码、"
                        "故障现象或需要了解的操作内容。"
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": (
                        "最多返回的相关知识片段数量。"
                    ),
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "alarm",
                        "equipment",
                        "sop",
                        "quality",
                    ],
                    "description": (
                        "可选知识分类。"
                        "alarm 表示报警处理知识；"
                        "equipment 表示设备资料；"
                        "sop 表示操作或维修 SOP；"
                        "quality 表示质量规范。"
                    ),
                },
            },
            required=[
                "query",
            ],
        ),
    )

    return registry


__all__ = ["ToolRegistry", "build_tool_registry"]
