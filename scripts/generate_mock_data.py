"""
ManuAgent MES Mock Data Generator

根据当前 SQLAlchemy 模型生成：
- 10 台设备
- 10 种物料
- 30 天生产数据（10 台设备 × 30 天 = 300 条）
- 50 条设备报警
- 20 张工单

输出目录：
    data/mock/

运行：
    python -m scripts.generate_mock_data

可选：
    python -m scripts.generate_mock_data --end-date 2026-09-15
    python -m scripts.generate_mock_data --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOCK_DIR = PROJECT_ROOT / "data" / "mock"

DEFAULT_RANDOM_SEED = 42
PRODUCTION_DAYS = 30
ALARM_COUNT = 50
WORK_ORDER_COUNT = 20


# ============================================================
# 通用工具
# ============================================================


def save_json(filename: str, data: list[dict[str, Any]]) -> None:
    MOCK_DIR.mkdir(parents=True, exist_ok=True)
    path = MOCK_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ {filename:<28} {len(data)} 条")


def random_datetime_on_date(target_date: date) -> datetime:
    return datetime.combine(
        target_date,
        time(
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        ),
    )


def iso_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat(timespec="seconds")


# ============================================================
# 1. 设备
# 对齐 Machine 模型：
# code / name / model / line_code / status / last_heartbeat_at
# ============================================================


def generate_machines(end_date: date) -> list[dict[str, Any]]:
    heartbeat_base = datetime.combine(end_date, time(18, 0, 0))

    rows = [
        ("MC-001", "CNC加工中心-01", "VMC-850", "LINE-A", "running"),
        ("MC-002", "CNC加工中心-02", "VMC-850", "LINE-A", "running"),
        ("MC-003", "数控车床-03", "CK6150", "LINE-A", "maintenance"),
        ("MC-004", "数控车床-04", "CK6150", "LINE-A", "running"),
        ("MC-005", "激光切割机-05", "LC-3015", "LINE-B", "running"),
        ("MC-006", "冲压机-06", "JH21-160", "LINE-B", "idle"),
        ("MC-007", "注塑机-07", "MA1600", "LINE-B", "running"),
        ("MC-008", "装配机器人-08", "IRB-6700", "LINE-C", "running"),
        ("MC-009", "包装机-09", "PK-500", "LINE-C", "running"),
        ("MC-010", "视觉检测设备-10", "VI-3000", "LINE-C", "running"),
    ]

    machines: list[dict[str, Any]] = []

    for index, (code, name, model, line_code, status) in enumerate(rows):
        # maintenance / offline 可故意设置心跳较旧，方便后续健康分析。
        if status == "maintenance":
            heartbeat = heartbeat_base - timedelta(hours=10 + index)
        elif status == "offline":
            heartbeat = None
        else:
            heartbeat = heartbeat_base - timedelta(minutes=random.randint(1, 25))

        machines.append(
            {
                "code": code,
                "name": name,
                "model": model,
                "line_code": line_code,
                "status": status,
                "last_heartbeat_at": iso_dt(heartbeat),
            }
        )

    return machines


# ============================================================
# 2. 物料
# 对齐 Material 模型：
# code / name / unit / stock_qty / safe_stock
# ============================================================


def generate_materials() -> list[dict[str, Any]]:
    # MAT-005 故意低于安全库存，作为库存风险样本。
    return [
        {"code": "MAT-001", "name": "铝合金板", "unit": "kg", "stock_qty": 850.00, "safe_stock": 300.00},
        {"code": "MAT-002", "name": "304不锈钢板", "unit": "kg", "stock_qty": 620.00, "safe_stock": 250.00},
        {"code": "MAT-003", "name": "45号钢棒", "unit": "kg", "stock_qty": 1200.00, "safe_stock": 400.00},
        {"code": "MAT-004", "name": "ABS塑料颗粒", "unit": "kg", "stock_qty": 450.00, "safe_stock": 200.00},
        {"code": "MAT-005", "name": "PP塑料颗粒", "unit": "kg", "stock_qty": 135.00, "safe_stock": 200.00},
        {"code": "MAT-006", "name": "M6螺丝", "unit": "pcs", "stock_qty": 8500.00, "safe_stock": 3000.00},
        {"code": "MAT-007", "name": "M8螺丝", "unit": "pcs", "stock_qty": 6200.00, "safe_stock": 2500.00},
        {"code": "MAT-008", "name": "轴承6204", "unit": "pcs", "stock_qty": 420.00, "safe_stock": 150.00},
        {"code": "MAT-009", "name": "包装纸箱", "unit": "pcs", "stock_qty": 780.00, "safe_stock": 300.00},
        {"code": "MAT-010", "name": "工业润滑油", "unit": "L", "stock_qty": 95.00, "safe_stock": 50.00},
    ]


# ============================================================
# 3. 生产记录
# 对齐 ProductionRecord 模型：
# machine_id（seed 时由 machine_code 转换）
# line_code / product_code / planned_qty / actual_qty /
# defect_qty / production_date
# ============================================================


def generate_production_records(
    machines: list[dict[str, Any]],
    end_date: date,
) -> list[dict[str, Any]]:
    product_mapping = {
        "MC-001": ["P-GEAR-A", "P-GEAR-B"],
        "MC-002": ["P-GEAR-A", "P-GEAR-B"],
        "MC-003": ["P-SHAFT-A", "P-SHAFT-B"],
        "MC-004": ["P-SHAFT-A", "P-SHAFT-B"],
        "MC-005": ["P-HOUSING-A", "P-BRACKET-A"],
        "MC-006": ["P-STAMP-A", "P-STAMP-B"],
        "MC-007": ["P-PLASTIC-A", "P-PLASTIC-B"],
        "MC-008": ["P-ASSEMBLY-A", "P-ASSEMBLY-B"],
        "MC-009": ["P-PACK-A", "P-PACK-B"],
        "MC-010": ["P-INSPECT-A", "P-INSPECT-B"],
    }

    records: list[dict[str, Any]] = []

    for day_index in range(PRODUCTION_DAYS):
        production_date = end_date - timedelta(
            days=PRODUCTION_DAYS - day_index - 1
        )
        days_from_end = (end_date - production_date).days

        for machine in machines:
            code = machine["code"]
            planned_qty = random.randint(400, 800)

            # MC-003：主要异常设备，最近 7 天进一步恶化。
            if code == "MC-003":
                if days_from_end <= 6:
                    achievement_rate = random.uniform(0.58, 0.72)
                    defect_rate = random.uniform(0.09, 0.14)
                else:
                    achievement_rate = random.uniform(0.68, 0.82)
                    defect_rate = random.uniform(0.06, 0.11)

            # MC-007：轻度异常设备。
            elif code == "MC-007":
                achievement_rate = random.uniform(0.76, 0.90)
                defect_rate = random.uniform(0.03, 0.07)

            # 其他设备：总体正常。
            else:
                achievement_rate = random.uniform(0.90, 1.02)
                defect_rate = random.uniform(0.005, 0.035)

            actual_qty = max(0, int(planned_qty * achievement_rate))
            defect_qty = min(
                actual_qty,
                max(0, int(actual_qty * defect_rate)),
            )

            records.append(
                {
                    "machine_code": code,
                    "line_code": machine["line_code"],
                    "product_code": random.choice(product_mapping[code]),
                    "planned_qty": planned_qty,
                    "actual_qty": actual_qty,
                    "defect_qty": defect_qty,
                    "production_date": production_date.isoformat(),
                }
            )

    return records


# ============================================================
# 4. 报警
# 对齐 MachineAlarm 模型：
# machine_id（seed 时由 machine_code 转换）
# alarm_code / alarm_message / level / started_at / ended_at
# ============================================================


def generate_alarms(
    machines: list[dict[str, Any]],
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    normal_templates = [
        ("E101", "主轴温度超过设定阈值", "high"),
        ("E102", "液压系统压力偏低", "medium"),
        ("E103", "驱动电机负载超过正常范围", "high"),
        ("E201", "设备传感器信号异常", "medium"),
        ("E301", "设备工业网络通信异常", "medium"),
        ("E401", "设备加工物料余量不足", "low"),
    ]

    mc003_templates = [
        ("E501", "主轴振动值持续超过预警阈值", "critical"),
        ("E101", "主轴轴承温度持续偏高", "high"),
        ("E103", "主轴驱动电机出现过载", "high"),
        ("E102", "液压系统压力低于正常范围", "medium"),
    ]

    codes = [m["code"] for m in machines]
    weights = [
        7 if code == "MC-003" else 4 if code == "MC-007" else 1
        for code in codes
    ]

    total_days = (end_date - start_date).days
    alarms: list[dict[str, Any]] = []

    for index in range(ALARM_COUNT):
        machine_code = random.choices(codes, weights=weights, k=1)[0]
        template = random.choice(
            mc003_templates if machine_code == "MC-003" else normal_templates
        )

        alarm_date = start_date + timedelta(
            days=random.randint(0, total_days)
        )
        started_at = random_datetime_on_date(alarm_date)

        level = template[2]
        unresolved_probability = {
            "low": 0.08,
            "medium": 0.15,
            "high": 0.25,
            "critical": 0.40,
        }[level]

        if random.random() < unresolved_probability:
            ended_at = None
        else:
            ended_at = started_at + timedelta(
                minutes=random.randint(5, 240)
            )

        alarms.append(
            {
                "machine_code": machine_code,
                "alarm_code": f"{template[0]}-{index + 1:03d}",
                "alarm_message": template[1],
                "level": level,
                "started_at": iso_dt(started_at),
                "ended_at": iso_dt(ended_at),
            }
        )

    alarms.sort(key=lambda item: item["started_at"])
    return alarms


# ============================================================
# 5. 工单
# 对齐 WorkOrder 模型：
# order_no / machine_id（seed 时转换）/ type / priority /
# description / status / assigned_to / created_at / updated_at
# ============================================================


def generate_work_orders(
    machines: list[dict[str, Any]],
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    general_templates = [
        ("maintenance", "按照设备保养计划执行检查、清洁和润滑。"),
        ("inspection", "检查传感器连接、信号和安装状态。"),
        ("inspection", "检查液压压力、油路以及密封情况。"),
        ("repair", "检查 PLC 及工业网络通信连接状态。"),
        ("inspection", "检查驱动电机温度、电流和负载情况。"),
    ]

    mc003_templates = [
        ("repair", "MC-003 多次出现主轴振动报警，检查主轴轴承、刀具夹持及机械结构。"),
        ("repair", "MC-003 主轴温度持续偏高，检查冷却系统、润滑状态及轴承温升。"),
        ("repair", "MC-003 出现驱动电机过载，检查电机、负载参数以及加工工况。"),
        ("inspection", "MC-003 液压压力异常，检查液压站压力、油泵、阀组及管路。"),
    ]

    codes = [m["code"] for m in machines]
    weights = [
        6 if code == "MC-003" else 3 if code == "MC-007" else 1
        for code in codes
    ]
    assignees = ["张工", "李工", "王工", "赵工"]
    total_days = (end_date - start_date).days
    end_dt = datetime.combine(end_date, time(23, 59, 59))

    work_orders: list[dict[str, Any]] = []

    for index in range(WORK_ORDER_COUNT):
        machine_code = random.choices(codes, weights=weights, k=1)[0]
        order_type, description = random.choice(
            mc003_templates if machine_code == "MC-003" else general_templates
        )

        created_date = start_date + timedelta(
            days=random.randint(0, total_days)
        )
        created_at = random_datetime_on_date(created_date)

        if machine_code == "MC-003":
            priority = random.choices(
                ["medium", "high", "urgent"],
                weights=[20, 50, 30],
                k=1,
            )[0]
        else:
            priority = random.choices(
                ["low", "medium", "high", "urgent"],
                weights=[20, 55, 20, 5],
                k=1,
            )[0]

        status = random.choices(
            ["completed", "in_progress", "pending", "cancelled"],
            weights=[55, 25, 15, 5],
            k=1,
        )[0]

        if status == "completed":
            updated_at = min(
                created_at + timedelta(hours=random.randint(1, 36)),
                end_dt,
            )
        elif status == "cancelled":
            updated_at = min(
                created_at + timedelta(hours=random.randint(1, 12)),
                end_dt,
            )
        else:
            updated_at = min(
                created_at + timedelta(hours=random.randint(0, 8)),
                end_dt,
            )

        work_orders.append(
            {
                "order_no": f"WO-{created_at.strftime('%Y%m%d')}-{index + 1:03d}",
                "machine_code": machine_code,
                "type": order_type,
                "priority": priority,
                "description": description,
                "status": status,
                "assigned_to": random.choice(assignees),
                "created_at": iso_dt(created_at),
                "updated_at": iso_dt(updated_at),
            }
        )

    work_orders.sort(key=lambda item: item["created_at"])
    return work_orders


# ============================================================
# 统计
# ============================================================


def print_statistics(
    machines: list[dict[str, Any]],
    materials: list[dict[str, Any]],
    production_records: list[dict[str, Any]],
    alarms: list[dict[str, Any]],
    work_orders: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 64)
    print("Mock 数据统计")
    print("=" * 64)
    print(f"设备数量：       {len(machines)}")
    print(f"物料数量：       {len(materials)}")
    print(f"生产记录：       {len(production_records)}")
    print(f"报警记录：       {len(alarms)}")
    print(f"维修工单：       {len(work_orders)}")

    mc003_records = [
        row for row in production_records
        if row["machine_code"] == "MC-003"
    ]
    planned = sum(row["planned_qty"] for row in mc003_records)
    actual = sum(row["actual_qty"] for row in mc003_records)
    defects = sum(row["defect_qty"] for row in mc003_records)

    achievement_rate = actual / planned * 100 if planned else 0
    defect_rate = defects / actual * 100 if actual else 0
    mc003_alarm_count = sum(
        1 for row in alarms if row["machine_code"] == "MC-003"
    )
    mc003_work_order_count = sum(
        1 for row in work_orders if row["machine_code"] == "MC-003"
    )

    print()
    print("预埋主要异常设备：MC-003")
    print(f"  生产达成率：{achievement_rate:.2f}%")
    print(f"  不良率：    {defect_rate:.2f}%")
    print(f"  报警数：    {mc003_alarm_count}")
    print(f"  工单数：    {mc003_work_order_count}")

    print()
    print("库存风险：")
    for material in materials:
        if material["stock_qty"] < material["safe_stock"]:
            print(
                f"  {material['code']} {material['name']}："
                f"{material['stock_qty']} < 安全库存 {material['safe_stock']}"
            )

    print("=" * 64)


# ============================================================
# 主流程
# ============================================================


def generate(end_date: date, random_seed: int) -> None:
    random.seed(random_seed)

    start_date = end_date - timedelta(days=PRODUCTION_DAYS - 1)

    print()
    print("=" * 64)
    print("ManuAgent MES Mock Data Generator")
    print("=" * 64)
    print(f"随机种子：{random_seed}")
    print(f"生产数据日期：{start_date.isoformat()} ~ {end_date.isoformat()}")
    print(f"输出目录：{MOCK_DIR}")
    print()

    machines = generate_machines(end_date)
    materials = generate_materials()
    production_records = generate_production_records(machines, end_date)
    alarms = generate_alarms(machines, start_date, end_date)
    work_orders = generate_work_orders(machines, start_date, end_date)

    print("正在生成 Mock JSON：")
    print()
    save_json("machines.json", machines)
    save_json("materials.json", materials)
    save_json("production_records.json", production_records)
    save_json("alarms.json", alarms)
    save_json("work_orders.json", work_orders)

    print_statistics(
        machines,
        materials,
        production_records,
        alarms,
        work_orders,
    )

    print()
    print("✓ Mock 数据生成完成")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ManuAgent MES mock data."
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=date.today().isoformat(),
        help="结束日期，格式 YYYY-MM-DD，默认今天",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="随机种子，默认 42",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        end_date = date.fromisoformat(args.end_date)
    except ValueError as exc:
        raise ValueError(
            "--end-date 必须使用 YYYY-MM-DD 格式，例如 2026-09-15"
        ) from exc

    generate(end_date=end_date, random_seed=args.seed)


if __name__ == "__main__":
    main()
