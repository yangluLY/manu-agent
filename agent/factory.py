from sqlalchemy.orm import Session

from agent.agent import ManuAgent
from agent.analytics.analyzer import DataAnalyzer
from agent.analytics.chart_generator import ChartGenerator
from agent.analytics.pipeline import BIPipeline
from agent.llm.deepseek_client import DeepSeekClient
from agent.registry import build_tool_registry
from agent.sql.corrector import SQLCorrector
from agent.sql.executor import SQLExecutor
from agent.sql.generator import SQLGenerator
from agent.sql.pipeline import SQLPipeline
from agent.sql.policies import READ_ONLY_ALLOWED_TABLES
from agent.sql.schema_provider import SchemaProvider
from agent.sql.validator import SQLValidator
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


def create_bi_pipeline(
    db: Session,
) -> BIPipeline:
    """基于当前请求的数据库绑定创建完整 BI 管线。"""

    bind = db.get_bind()
    engine = getattr(bind, "engine", bind)
    llm = DeepSeekClient()

    schema_provider = SchemaProvider(
        engine=engine,
        allowed_tables=READ_ONLY_ALLOWED_TABLES,
    )
    generator = SQLGenerator(
        llm=llm,
        schema_provider=schema_provider,
    )
    validator = SQLValidator(
        allowed_tables=READ_ONLY_ALLOWED_TABLES,
    )
    executor = SQLExecutor(
        engine=engine,
        validator=validator,
    )
    corrector = SQLCorrector(
        llm=llm,
        schema_provider=schema_provider,
    )

    return BIPipeline(
        sql_pipeline=SQLPipeline(
            generator=generator,
            corrector=corrector,
            executor=executor,
            max_retries=2,
        ),
        analyzer=DataAnalyzer(llm=llm),
        chart_generator=ChartGenerator(llm=llm),
    )
