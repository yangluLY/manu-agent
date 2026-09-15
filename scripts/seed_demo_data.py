"""
ManuAgent MES Demo Data Seeder

读取 data/mock/ 下的数据并写入 PostgreSQL。

导入顺序：
1. machines
2. materials
3. production_records
4. machine_alarms
5. work_orders

运行：
    python -m scripts.seed_demo_data
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from services.database.session import SessionLocal
from services.database.models.machine import Machine
from services.database.models.material import Material
from services.database.models.production_record import ProductionRecord
from services.database.models.alarm import MachineAlarm
from services.database.models.work_order import WorkOrder


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOCK_DIR = PROJECT_ROOT / "data" / "mock"


# ============================================================
# JSON / 类型转换
# ============================================================


def load_json(filename: str) -> list[dict[str, Any]]:
    path = MOCK_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"找不到 Mock 数据文件：{path}\n"
            "请先执行：python -m scripts.generate_mock_data"
        )

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{filename} 的根节点必须是 JSON 数组")

    return data


def parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def to_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


# ============================================================
# 防重复
# ============================================================


def check_existing_demo_data(db: Session) -> None:
    """
    检测这批 Demo 数据是否已经导入过。

    为避免误删用户已有数据，这里不自动清库。
    """
    demo_machine_codes = [f"MC-{i:03d}" for i in range(1, 11)]
    demo_material_codes = [f"MAT-{i:03d}" for i in range(1, 11)]

    existing_machine = db.scalar(
        select(Machine.code).where(Machine.code.in_(demo_machine_codes)).limit(1)
    )
    existing_material = db.scalar(
        select(Material.code).where(Material.code.in_(demo_material_codes)).limit(1)
    )

    if existing_machine or existing_material:
        found = existing_machine or existing_material
        raise RuntimeError(
            f"检测到 Demo 编码已存在：{found}\n"
            "为避免重复插入，本次 seed 已停止。\n"
            "如果这些是之前测试数据，请先通过现有 API 或数据库手动清理后再执行。"
        )


# ============================================================
# machine_code -> machine_id
# ============================================================


def get_machine_id(machine_code: str, machine_map: dict[str, int]) -> int:
    machine_id = machine_map.get(machine_code)

    if machine_id is None:
        raise ValueError(
            f"Mock 数据引用了不存在的设备编码：{machine_code}"
        )

    return machine_id


# ============================================================
# 1. Machine
# ============================================================


def seed_machines(db: Session) -> dict[str, int]:
    data = load_json("machines.json")
    machines: list[Machine] = []

    for item in data:
        machine = Machine(
            code=item["code"],
            name=item["name"],
            model=item.get("model"),
            line_code=item.get("line_code"),
            status=item.get("status", "offline"),
            last_heartbeat_at=parse_datetime(item.get("last_heartbeat_at")),
        )
        db.add(machine)
        machines.append(machine)

    # 先 INSERT 但暂不 COMMIT，以获得 PostgreSQL 生成的自增 id。
    db.flush()

    machine_map = {
        machine.code: machine.id
        for machine in machines
    }

    print(f"✓ 导入设备：{len(machines)} 台")
    return machine_map


# ============================================================
# 2. Material
# ============================================================


def seed_materials(db: Session) -> None:
    data = load_json("materials.json")

    for item in data:
        material = Material(
            code=item["code"],
            name=item["name"],
            unit=item["unit"],
            stock_qty=to_decimal(item["stock_qty"]),
            safe_stock=to_decimal(item["safe_stock"]),
        )
        db.add(material)

    db.flush()
    print(f"✓ 导入物料：{len(data)} 种")


# ============================================================
# 3. ProductionRecord
# ============================================================


def seed_production_records(
    db: Session,
    machine_map: dict[str, int],
) -> None:
    data = load_json("production_records.json")

    for item in data:
        record = ProductionRecord(
            machine_id=get_machine_id(item["machine_code"], machine_map),
            line_code=item["line_code"],
            product_code=item["product_code"],
            planned_qty=item["planned_qty"],
            actual_qty=item["actual_qty"],
            defect_qty=item["defect_qty"],
            production_date=parse_date(item["production_date"]),
        )
        db.add(record)

    db.flush()
    print(f"✓ 导入生产记录：{len(data)} 条")


# ============================================================
# 4. MachineAlarm
# ============================================================


def seed_alarms(
    db: Session,
    machine_map: dict[str, int],
) -> None:
    data = load_json("alarms.json")

    for item in data:
        alarm = MachineAlarm(
            machine_id=get_machine_id(item["machine_code"], machine_map),
            alarm_code=item["alarm_code"],
            alarm_message=item["alarm_message"],
            level=item.get("level", "medium"),
            started_at=parse_datetime(item["started_at"]),
            ended_at=parse_datetime(item.get("ended_at")),
        )
        db.add(alarm)

    db.flush()
    print(f"✓ 导入报警：{len(data)} 条")


# ============================================================
# 5. WorkOrder
# ============================================================


def seed_work_orders(
    db: Session,
    machine_map: dict[str, int],
) -> None:
    data = load_json("work_orders.json")

    for item in data:
        work_order = WorkOrder(
            order_no=item["order_no"],
            machine_id=get_machine_id(item["machine_code"], machine_map),
            type=item.get("type", "maintenance"),
            priority=item.get("priority", "medium"),
            description=item["description"],
            status=item.get("status", "pending"),
            assigned_to=item.get("assigned_to"),
            created_at=parse_datetime(item.get("created_at")) or datetime.utcnow(),
            updated_at=parse_datetime(item.get("updated_at")) or datetime.utcnow(),
        )
        db.add(work_order)

    db.flush()
    print(f"✓ 导入工单：{len(data)} 张")


# ============================================================
# 数据库统计 / 简单验收
# ============================================================


def print_database_statistics(db: Session) -> None:
    machine_count = db.scalar(select(func.count()).select_from(Machine)) or 0
    material_count = db.scalar(select(func.count()).select_from(Material)) or 0
    production_count = (
        db.scalar(select(func.count()).select_from(ProductionRecord)) or 0
    )
    alarm_count = db.scalar(select(func.count()).select_from(MachineAlarm)) or 0
    work_order_count = db.scalar(select(func.count()).select_from(WorkOrder)) or 0

    print()
    print("=" * 64)
    print("数据库数据统计")
    print("=" * 64)
    print(f"设备：      {machine_count}")
    print(f"物料：      {material_count}")
    print(f"生产记录：  {production_count}")
    print(f"报警：      {alarm_count}")
    print(f"工单：      {work_order_count}")
    print("=" * 64)


def print_demo_validation(db: Session) -> None:
    """
    验证预埋异常是否进入数据库。
    """
    mc003_id = db.scalar(
        select(Machine.id).where(Machine.code == "MC-003")
    )

    if mc003_id is None:
        return

    rows = db.scalars(
        select(ProductionRecord).where(
            ProductionRecord.machine_id == mc003_id
        )
    ).all()

    planned = sum(row.planned_qty for row in rows)
    actual = sum(row.actual_qty for row in rows)
    defects = sum(row.defect_qty for row in rows)

    achievement_rate = actual / planned * 100 if planned else 0
    defect_rate = defects / actual * 100 if actual else 0

    alarm_count = db.scalar(
        select(func.count())
        .select_from(MachineAlarm)
        .where(MachineAlarm.machine_id == mc003_id)
    ) or 0

    work_order_count = db.scalar(
        select(func.count())
        .select_from(WorkOrder)
        .where(WorkOrder.machine_id == mc003_id)
    ) or 0

    risky_materials = db.scalars(
        select(Material).where(Material.stock_qty < Material.safe_stock)
    ).all()

    print()
    print("Demo 异常数据验收：")
    print(f"  MC-003 生产达成率：{achievement_rate:.2f}%")
    print(f"  MC-003 不良率：    {defect_rate:.2f}%")
    print(f"  MC-003 报警数：    {alarm_count}")
    print(f"  MC-003 工单数：    {work_order_count}")

    for material in risky_materials:
        print(
            f"  库存风险：{material.code} {material.name} "
            f"stock={material.stock_qty}, safe={material.safe_stock}"
        )


# ============================================================
# 主流程
# ============================================================


def seed() -> None:
    print()
    print("=" * 64)
    print("ManuAgent MES Demo Data Seeder")
    print("=" * 64)
    print(f"Mock 数据目录：{MOCK_DIR}")
    print()

    db = SessionLocal()

    try:
        check_existing_demo_data(db)

        machine_map = seed_machines(db)

        print()
        print("设备 ID 映射：")
        for code, machine_id in machine_map.items():
            print(f"  {code} -> {machine_id}")
        print()

        seed_materials(db)
        seed_production_records(db, machine_map)
        seed_alarms(db, machine_map)
        seed_work_orders(db, machine_map)

        # 五类数据全部成功后，只提交一次。
        # 任一环节异常都会进入 except 并整体 rollback。
        db.commit()

        print()
        print("✓ 所有 Mock 数据已写入 PostgreSQL")

        print_database_statistics(db)
        print_demo_validation(db)

        print()
        print("✓ Demo 数据初始化完成")
        print()

    except Exception as exc:
        db.rollback()

        print()
        print("=" * 64)
        print("❌ Demo 数据初始化失败")
        print("=" * 64)
        print(exc)
        print()

        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()
