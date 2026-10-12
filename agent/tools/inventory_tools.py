from agent.tools.serializers import serialize_material
from agent.tools.types import ToolResult
from services.mes.inventory_service import InventoryService


class InventoryTools:
    """Read-only material and stock-risk tools."""

    def __init__(self, inventory_service: InventoryService):
        self.inventory_service = inventory_service

    def get_low_stock_materials(self) -> ToolResult:
        materials = self.inventory_service.get_low_stock_materials()

        return ToolResult.ok(
            {
                "count": len(materials),
                "materials": [
                    serialize_material(material)
                    for material in materials
                ],
            }
        )
