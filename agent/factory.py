from sqlalchemy.orm import Session

from agent.agent import ManuAgent
from agent.llm.deepseek_client import DeepSeekClient
from agent.registry import build_tool_registry
from agent.tools.alarm_tools import AlarmTools
from agent.tools.inventory_tools import InventoryTools
from agent.tools.knowledge_tools import KnowledgeTools
from agent.tools.machine_tools import MachineTools
from agent.tools.production_tools import ProductionTools
from agent.tools.work_order_tools import WorkOrderTools
from knowledge.retrieval.retriever import (
    KnowledgeRetriever,
)
from services.mes.alarm_service import AlarmService
from services.mes.inventory_service import InventoryService
from services.mes.machine_service import MachineService
from services.mes.production_service import ProductionService
from services.mes.work_order_service import WorkOrderService


def create_manu_agent(
    db: Session,
) -> ManuAgent:

    # Service
    machine_service = MachineService(db)
    alarm_service = AlarmService(db)
    inventory_service = InventoryService(db)
    work_order_service = WorkOrderService(db)
    production_service = ProductionService(db)
    knowledge_retriever = KnowledgeRetriever(db=db,)

    # Tool
    machine_tools = MachineTools(
        machine_service=machine_service,
    )

    alarm_tools = AlarmTools(
        alarm_service=alarm_service,
        machine_service=machine_service,
    )

    inventory_tools = InventoryTools(
        inventory_service=inventory_service,
    )

    work_order_tools = WorkOrderTools(
        work_order_service=work_order_service,
        machine_service=machine_service,
    )

    production_tools = ProductionTools(
        production_service=production_service,
        machine_service=machine_service,
    )

    knowledge_tools = KnowledgeTools(
        retriever=knowledge_retriever,
    )

    # Registry
    registry = build_tool_registry(
        machine_tools=machine_tools,
        alarm_tools=alarm_tools,
        inventory_tools=inventory_tools,
        work_order_tools=work_order_tools,
        production_tools=production_tools,
        knowledge_tools=knowledge_tools,
    )

    # LLM
    llm = DeepSeekClient()

    return ManuAgent(
        registry=registry,
        llm=llm,
    )