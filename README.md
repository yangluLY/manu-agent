# ManuAgent

ManuAgent 是一个面向智能制造场景的 AI Agent 项目。

当前阶段先搭建一个轻量级 MES 后端，提供设备、报警、工单、库存、生产记录等基础能力，后续再接入数据分析、Agent Tools 和大模型，实现自然语言查询、生产分析和业务操作。

例如未来可以支持：

```text
最近 30 天哪台设备风险最高？

MC-003 为什么生产效率低？

哪些物料低于安全库存？

给 MC-003 创建一张维修工单。
```

---

# Architecture

当前整体架构：

```text
Client
  ↓
FastAPI Router
  ↓
Service
  ↓
Repository
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

后续 Agent 架构：

```text
User
  ↓
ManuAgent
  ↓
Agent Tools / Analytics
  ↓
Service
  ↓
Repository
  ↓
PostgreSQL
```

主要目录：

```text
manu-agent/
├── apps/
│   └── api/
│       └── app/
│           ├── core/
│           ├── routers/
│           ├── schemas/
│           └── main.py
│
├── services/
│   ├── database/
│   │   ├── models/
│   │   └── repositories/
│   └── mes/
│
├── data/
│   └── mock/
│
├── scripts/
│   ├── generate_mock_data.py
│   └── seed_demo_data.py
│
├── tests/
│   └── api/
│
└── README.md
```

---

# Technology Stack

后端：

```text
Python
FastAPI
Pydantic
SQLAlchemy
```

数据库：

```text
PostgreSQL
```

开发环境：

```text
Docker
Docker Desktop
VS Code
```

测试：

```text
pytest
FastAPI TestClient
SQLite 内存数据库
```

---

# Local Development

## 1. 创建虚拟环境

```bash
python -m venv .venv
```

Windows 激活：

```bash
.venv\Scripts\activate
```

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 3. 启动 PostgreSQL

如果使用 Docker Compose：

```bash
docker compose up -d
```

查看容器：

```bash
docker ps
```

## 4. 生成 Mock 数据

```bash
python -m scripts.generate_mock_data
```

生成：

```text
data/mock/
├── machines.json
├── materials.json
├── production_records.json
├── alarms.json
└── work_orders.json
```

当前 Demo 数据包括：

```text
10 台设备
10 种物料
300 条生产记录
50 条报警
20 张工单
```

## 5. 导入 PostgreSQL

```bash
python -m scripts.seed_demo_data
```

## 6. 启动 FastAPI

```bash
uvicorn apps.api.app.main:app --reload
```

Swagger：

```text
http://127.0.0.1:8000/docs
```

## 7. 运行测试

```bash
python -m pytest -v
```

---

# Database

当前主要数据表：

```text
machines
machine_alarms
work_orders
materials
production_records
```

主要关系：

```text
Machine
 ├── MachineAlarm
 ├── WorkOrder
 └── ProductionRecord

Material
 └── 库存信息
```

主要业务数据：

```text
Machine
设备基础信息、产线、状态

MachineAlarm
设备报警、报警等级、开始和结束时间

WorkOrder
维修、保养、巡检工单

Material
当前库存、安全库存

ProductionRecord
计划产量、实际产量、不良数量、生产日期
```

Mock 数据中预设了一些异常：

```text
MC-003
├── 生产达成率较低
├── 不良率较高
├── 报警较多
└── 维修工单较多

MC-007
└── 轻度异常

MAT-005
└── 当前库存低于安全库存
```

用于后续 Analytics 和 Agent 分析。

---

# API

当前主要 API 能力：

## Health

```http
GET /health
```

## Machine

```http
GET /machines
GET /machines/{machine_id}
POST /machines
```

设备不存在：

```json
{
  "detail": "Machine not found"
}
```

HTTP：

```text
404
```

设备编码重复：

```json
{
  "detail": "Machine code already exists"
}
```

HTTP：

```text
409
```

## Alarm

支持查询设备报警：

```text
按设备查询报警
查看报警等级
查看历史报警和未恢复报警
```

## Work Order

支持：

```text
创建维修工单
创建保养工单
创建巡检工单
```

## Material

支持：

```text
库存查询
低库存查询
```

低库存判断：

```text
stock_qty < safe_stock
```

## Production Record

支持生产记录管理：

```text
计划产量
实际产量
不良数量
生产日期
```

完整接口可查看：

```text
http://127.0.0.1:8000/docs
```

---

# Testing

目前已经覆盖：

```text
Health Check

Machine List
Machine Detail
Create Machine
Machine Not Found
Duplicate Machine

Alarm Query

Create Work Order

Low Stock
```

运行：

```bash
python -m pytest -v
```

测试使用独立数据库，不影响 PostgreSQL Demo 数据。

---

# Roadmap

## V0：MES 基础能力

已完成：

```text
FastAPI 项目结构
PostgreSQL
SQLAlchemy Models
Repository
Service
Machine API
Alarm API
Work Order API
Material API
Production Record API
Mock Data
Seed Data
pytest API 测试
统一异常处理
404 / 409 错误处理
```

## V1：制造数据分析

计划实现：

```text
生产达成率
不良率
设备生产趋势
报警频率
工单统计
库存风险
设备健康评分
```

计划目录：

```text
services/analytics/
├── machine_analytics.py
├── production_analytics.py
├── alarm_analytics.py
├── inventory_analytics.py
└── work_order_analytics.py
```

## V2：Agent Tools

将现有 MES 能力封装成 Agent 可调用工具：

```text
get_machine_detail
get_machine_production_stats
get_machine_alarms
get_machine_work_orders
get_low_stock_materials
create_work_order
```

## V3：ManuAgent

实现自然语言驱动的制造分析。

例如：

```text
分析最近 30 天生产情况，
告诉我哪些设备需要重点关注。
```

Agent 自动完成：

```text
查询设备
  ↓
查询生产记录
  ↓
查询报警
  ↓
查询工单
  ↓
分析风险
  ↓
生成结论和建议
```

## V4：企业级能力

后续计划：

```text
MES / ERP 集成
IoT 实时设备数据
权限管理
审计日志
Agent 执行记录
Human-in-the-loop
可观测性
Agent Evaluation
```

---

# 当前阶段

当前项目已经完成：

```text
Mock Data
   ↓
PostgreSQL
   ↓
Repository
   ↓
Service
   ↓
FastAPI
   ↓
pytest
```

下一阶段：

```text
Analytics
   ↓
Agent Tools
   ↓
ManuAgent
```
