# ManuAgent

ManuAgent 是一个面向智能制造场景的 AI Agent 项目。

项目从传统 MES 后端逐步演进，目前 V1 已支持基于 DeepSeek 的 Tool Calling，可以通过自然语言查询设备、报警、库存、生产工单和生产记录等实时业务数据。

## Architecture

V1 在原有 MES 后端基础上增加 Agent 层。

```text
User
 ↓
POST /api/v1/agent/chat
 ↓
ManuAgent
 ↓
DeepSeek LLM
 ↓
Tool Calling
 ↓
Tool Registry
 ↓
Tool Executor
 ↓
Agent Tools
 ├── Machine Tools
 ├── Alarm Tools
 ├── Inventory Tools
 ├── Work Order Tools
 └── Production Tools
 ↓
MES Services
 ↓
Repositories
 ↓
PostgreSQL
```

项目采用分层设计：

```text
apps/api/
├── routers/              HTTP API
└── schemas/              Request / Response Schema

agent/
├── tools/                LLM 可调用的业务工具
├── llm/                  DeepSeek API Client
├── prompts/              Agent System Prompt
├── registry.py           Tool 注册中心
├── executor.py           Tool 执行器
├── factory.py            Agent 依赖组装
└── agent.py              Agent 主循环

services/
├── mes/                  MES 业务逻辑
└── database/
    ├── models/           SQLAlchemy Models
    └── repositories/     数据访问层

scripts/
└── test_agent.py         Agent 集成测试
```

### Agent Execution Flow

```text
用户问题
 ↓
DeepSeek 判断是否需要实时业务数据
 ↓
选择 Tool
 ↓
生成 Function Call
 ↓
ManuAgent 接收 Function Call
 ↓
ToolExecutor 执行 Tool
 ↓
Tool 调用 MES Service
 ↓
Repository 查询 PostgreSQL
 ↓
返回结构化 ToolResult
 ↓
ToolResult 返回 DeepSeek
 ↓
DeepSeek 生成最终自然语言回答
```

Tool 只负责获取真实业务数据，不负责生成最终自然语言。

例如：

```text
用户：
CNC-001 当前是什么状态？

DeepSeek：
调用 get_machine_status

Tool Result：
{
  "success": true,
  "data": {
    "code": "CNC-001",
    "status": "RUNNING"
  }
}

DeepSeek：
CNC-001 当前处于运行状态。
```

实时 MES 数据必须通过 Tool 查询，禁止由模型自行猜测或编造。

## Technology Stack

```text
Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy

Database
- PostgreSQL

AI
- DeepSeek API
- Responses API
- Function / Tool Calling

Infrastructure
- Docker
- Docker Compose

Testing
- Pytest
- Agent Integration Test
```

## Local Development

创建并激活 Python 虚拟环境：

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

配置 DeepSeek API Key：

```powershell
$env:DEEPSEEK_API_KEY="your-api-key"
```

启动数据库：

```bash
docker compose up -d
```

启动 FastAPI：

```bash
uvicorn apps.api.app.main:app --reload
```

打开 Swagger：

```text
http://127.0.0.1:8000/docs
```

## Agent API

### POST `/api/v1/agent/chat`

Request：

```json
{
  "message": "CNC-001 当前是什么状态？"
}
```

Response：

```json
{
  "answer": "CNC-001 当前处于运行状态。"
}
```

## Agent Integration Test

运行：

```bash
python -m scripts.test_agent
```

该测试直接验证：

```text
DeepSeek
 ↓
Tool Calling
 ↓
ToolExecutor
 ↓
MES Service
 ↓
PostgreSQL
 ↓
ToolResult
 ↓
DeepSeek Final Answer
```

## Roadmap

```text
V0
MES Backend
✅

V1
DeepSeek + Tool Calling Agent
✅

V2
RAG Knowledge Base
🚧

V3
Tool Calling + RAG Hybrid Agent

V4
Workflow / Planning / Multi-Agent
```

V2 将增加企业知识库能力，用于设备说明书、报警手册、维修 SOP 和生产知识检索，并与 V1 的实时 MES Tool Calling 融合。
