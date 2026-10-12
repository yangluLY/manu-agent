from datetime import date
from decimal import Decimal
from inspect import Parameter, signature

from agent.executor import ToolExecutor
from agent.registry import build_tool_registry
from agent.tools.alarm_tools import AlarmTools
from agent.tools.inventory_tools import InventoryTools
from agent.tools.machine_tools import MachineTools
from agent.tools.production_tools import ProductionTools
from agent.tools.work_order_tools import WorkOrderTools
from services.database.models.machine import Machine
from services.mes.alarm_service import AlarmService
from services.mes.inventory_service import InventoryService
from services.mes.machine_service import MachineService
from services.mes.production_service import ProductionService
from services.mes.work_order_service import WorkOrderService


def build_tools(db_session):
    machine_service = MachineService(db_session)
    alarm_service = AlarmService(db_session)
    production_service = ProductionService(db_session)
    inventory_service = InventoryService(db_session)
    work_order_service = WorkOrderService(db_session)

    machine_tools = MachineTools(machine_service)
    alarm_tools = AlarmTools(alarm_service, machine_service)
    production_tools = ProductionTools(production_service, machine_service)
    inventory_tools = InventoryTools(inventory_service)
    work_order_tools = WorkOrderTools(work_order_service, machine_service)

    registry = build_tool_registry(
        machine_tools=machine_tools,
        alarm_tools=alarm_tools,
        production_tools=production_tools,
        inventory_tools=inventory_tools,
        work_order_tools=work_order_tools,
    )

    return {
        "machine": machine_tools,
        "alarm": alarm_tools,
        "production": production_tools,
        "inventory": inventory_tools,
        "work_order": work_order_tools,
        "registry": registry,
        "services": {
            "alarm": alarm_service,
            "production": production_service,
            "inventory": inventory_service,
        },
    }


def seed_machine(db_session) -> Machine:
    machine = Machine(
        code="MC-AGENT-001",
        name="Agent 测试设备",
        model="VMC-850",
        line_code="LINE-A",
        status="running",
    )
    db_session.add(machine)
    db_session.commit()
    db_session.refresh(machine)
    return machine


def test_registry_uses_responses_function_schema_without_strict(db_session):
    tools = build_tools(db_session)
    schemas = tools["registry"].schemas

    assert {schema["name"] for schema in schemas} == {
        "list_machines",
        "get_machine_by_code",
        "get_machine_detail",
        "get_machine_status",
        "get_machine_production_stats",
        "get_machine_alarms",
        "get_machine_work_orders",
        "get_low_stock_materials",
        "create_work_order",
    }
    assert all(schema["type"] == "function" for schema in schemas)
    assert all("strict" not in schema for schema in schemas)
    assert all("parameters" in schema for schema in schemas)


def test_registry_schema_parameters_match_tool_method_signatures(db_session):
    tools = build_tools(db_session)
    registry = tools["registry"]
    expected_names = {
        name
        for tool_key in (
            "machine",
            "alarm",
            "production",
            "inventory",
            "work_order",
        )
        for name, method in vars(type(tools[tool_key])).items()
        if callable(method) and not name.startswith("_")
    }

    assert set(registry.tool_names) == expected_names

    for schema in registry.schemas:
        handler = registry.get_handler(schema["name"])
        assert handler is not None

        method_parameters = signature(handler).parameters
        schema_parameters = schema["parameters"]
        assert set(schema_parameters["properties"]) == set(method_parameters)
        assert set(schema_parameters["required"]) == {
            name
            for name, parameter in method_parameters.items()
            if parameter.default is Parameter.empty
        }


def test_machine_and_production_tools_return_structured_data(db_session):
    machine = seed_machine(db_session)
    tools = build_tools(db_session)

    tools["services"]["production"].create_record(
        machine_id=machine.id,
        line_code="LINE-A",
        product_code="PRODUCT-A01",
        planned_qty=100,
        actual_qty=95,
        defect_qty=2,
        production_date=date(2026, 9, 15),
    )

    detail = tools["machine"].get_machine_detail("mc-agent-001")
    stats = tools["production"].get_machine_production_stats(
        "MC-AGENT-001",
        start_date="2026-09-01",
        end_date="2026-09-30",
    )

    assert detail.success is True
    assert detail.data["code"] == "MC-AGENT-001"
    assert stats.success is True
    assert stats.data["summary"]["planned_qty"] == 100
    assert stats.data["summary"]["completion_rate"] == 95.0


def test_alarm_inventory_and_work_order_tools(db_session):
    machine = seed_machine(db_session)
    tools = build_tools(db_session)

    tools["services"]["alarm"].create_alarm(
        machine_id=machine.id,
        alarm_code="E101",
        alarm_message="主轴温度过高",
        level="high",
    )
    tools["services"]["inventory"].create_material(
        code="MAT-AGENT-001",
        name="测试物料",
        unit="kg",
        stock_qty=Decimal("10"),
        safe_stock=Decimal("20"),
    )

    alarms = tools["alarm"].get_machine_alarms(
        "MC-AGENT-001",
        active_only=True,
    )
    materials = tools["inventory"].get_low_stock_materials()
    created = tools["work_order"].create_work_order(
        machine_code="MC-AGENT-001",
        type="repair",
        priority="high",
        description="检查主轴冷却系统",
        assigned_to="张工",
    )
    work_orders = tools["work_order"].get_machine_work_orders(
        "MC-AGENT-001",
        open_only=True,
    )

    assert alarms.success is True
    assert alarms.data["count"] == 1
    assert alarms.data["alarms"][0]["active"] is True
    assert materials.success is True
    assert materials.data["materials"][0]["shortage_qty"] == 10.0
    assert created.success is True
    assert created.data["status"] == "pending"
    assert work_orders.success is True
    assert work_orders.data["count"] == 1


def test_invalid_date_is_returned_as_tool_error(db_session):
    seed_machine(db_session)
    tools = build_tools(db_session)

    result = tools["production"].get_machine_production_stats(
        "MC-AGENT-001",
        start_date="2026/09/01",
    )

    assert result.success is False
    assert result.error.code == "INVALID_DATE_FORMAT"


def test_executor_dispatches_registered_tool(db_session):
    seed_machine(db_session)
    tools = build_tools(db_session)
    executor = ToolExecutor(tools["registry"])

    result = executor.execute(
        "get_machine_detail",
        {"machine_code": "MC-AGENT-001"},
    )

    assert result.success is True
    assert result.data["name"] == "Agent 测试设备"
