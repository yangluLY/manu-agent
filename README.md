# ManuAgent 智能制造协同平台

ManuAgent 是面向制造场景的全栈 AI 应用，将设备、报警、工单、库存和生产记录等 MES 数据，与自然语言对话、知识库检索、智能 BI 和多步骤工作流结合，提供统一的生产管理与分析入口。

本文根据当前仓库实现整理。演示数据来自本地 Mock 数据集，真实设备接入和 ERP 对接等需要另行实现。

## 1. 系统功能

| 模块 | 当前能力 | 前端入口 |
| --- | --- | --- |
| 登录认证 | 用户名密码登录、JWT 认证、退出登录；当前标签页刷新恢复登录状态 | `/login` |
| 设备管理 | 设备列表、详情、新增、编辑、删除及关联数据查询 | `/equipment` |
| 生产管理 | 生产记录查询与维护，计划产量、实际产量、不良数量等统计 | `/production` |
| 库存管理 | 物料查询、库存调整、入库、出库和安全库存预警 | `/inventory` |
| 工单管理 | 维修、保养、巡检工单查询与创建，状态流转和关闭 | `/work-orders` |
| 报警管理 | 报警查询、创建和恢复处理，关联设备查询 | 设备相关功能及 API |
| AI 对话 | 调用 MES 和知识库工具回答问题，支持多轮上下文和流式输出 | `/chat` |
| 对话历史 | 本地保存、查看和继续对话 | `/conversations` |
| 智能 BI | 自然语言生成只读 SQL，查询、分析并生成 ECharts 图表；不适合绘图时显示表格 | `/bi` |
| 知识库 RAG | TXT、Markdown、PDF 加载、分块、向量检索与带来源回答；文档列表、状态和重新入库接口 | AI 对话及知识库 API |
| 工作流 Agent | 问题路由、任务规划、MES / RAG / BI 步骤执行、汇总、SSE 事件流与持久化 Checkpoint | `/workflow` |

可以尝试：

```text
查询 MC-003 的设备信息和最近的报警。
哪些物料低于安全库存？
查询报警次数最多的 5 台设备，并生成图表。
伺服过载报警应该如何处理？
结合生产记录和报警信息，分析 MC-003 需要重点关注的问题。
```

### 当前实现边界

- 前端业务页面需要登录，后端工作流执行接口校验 JWT 和线程归属。MES、普通 Agent、BI、知识库接口尚未统一接入认证，前端登录保护不能替代后端权限控制。
- 已包含审批、恢复、审计及历史管理模块与测试，但 `main.py` 未挂载 `workflow_management.router`，前端也未注册工作流历史页面，不能将其视为已开放的页面功能。
- 当前持久化工作流工厂设置 `require_approval=False`，并非所有工作流都会进入人工审批。
- 普通聊天历史保存在浏览器本地，工作流执行状态保存在 PostgreSQL Checkpoint，两者是不同的数据链路。

## 2. 架构设计

### 整体架构

```mermaid
flowchart TD
    Browser[浏览器：React / TypeScript / Ant Design]
    API[FastAPI：业务接口 / JWT / 流式响应]
    MES[MES Service]
    Repo[Repository / SQLAlchemy]
    Chat[Agent：工具注册与调用循环]
    Workflow[LangGraph：路由 / 规划 / 执行 / 汇总]
    BI[BI：SQL 生成 / 校验 / 查询 / 纠错 / 分析 / 图表]
    RAG[RAG：分块 / 向量检索 / 来源引用]
    LLM[DeepSeek：通过 OpenAI SDK 调用]
    DB[(PostgreSQL / pgvector)]
    CP[(Checkpoint / 工作流线程)]
    Browser --> API
    API --> MES --> Repo --> DB
    API --> Chat
    API --> Workflow
    API --> BI
    API --> RAG
    Chat --> MES
    Chat --> RAG
    Chat --> LLM
    Workflow --> MES
    Workflow --> BI
    Workflow --> RAG
    Workflow --> LLM
    Workflow --> CP
    BI --> LLM
    BI --> DB
    RAG --> DB
    RAG --> LLM
```

### 主要处理链路

- **MES：** Router 校验请求，Service 处理业务规则，Repository 负责数据访问，SQLAlchemy 映射 PostgreSQL 表。
- **AI 对话：** 问题和历史上下文进入 Agent，模型选择设备、报警、生产、库存、工单或知识库工具，执行后生成回答。普通聊天流式接口使用 NDJSON。
- **智能 BI：** Schema Discovery → Text-to-SQL → SQL Safety → SQL Executor → Retry / Correction → Data Analyst → Chart Generator → ECharts。通过 SQLGlot 和只读表策略限制 SQL 查询。
- **知识库：** 文档加载 → 分块 → BGE 中文模型生成 512 维向量 → pgvector 存储 → 相似度检索 → 结合检索内容回答。默认模型为 `BAAI/bge-small-zh-v1.5`。
- **工作流：** LangGraph 根据问题路由并规划任务，执行 MES / RAG / BI 步骤，汇总结果；通过 `thread_id` 关联持久化状态，以 SSE 推送执行事件。

### 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | React 19、TypeScript、Vite、React Router、Ant Design、Axios |
| 图表 | ECharts、echarts-for-react |
| API | Python、FastAPI、Pydantic、Pydantic Settings |
| 数据访问 | SQLAlchemy、Alembic、Psycopg |
| 数据库 | PostgreSQL 16、pgvector |
| 大模型与编排 | OpenAI Python SDK、DeepSeek、LangGraph、PostgreSQL Checkpointer |
| 知识检索 | Sentence Transformers、BGE、pgvector、PyPDF |
| 认证 | PyJWT、pwdlib / Argon2 |
| 测试 | pytest、FastAPI TestClient、SQLite、独立 PostgreSQL 集成测试 |

### 目录结构

```text
manu-agent/
├── frontend/                 # React 页面、路由、API 客户端与样式
├── apps/api/app/
│   ├── main.py               # FastAPI 入口与路由注册
│   ├── core/                 # 配置、异常及统一异常处理
│   ├── dependencies/         # 认证、数据库与工作流依赖
│   ├── routers/              # MES、Agent、BI、知识库及工作流接口
│   └── schemas/              # 请求和响应模型
├── services/
│   ├── mes/                  # MES 业务服务
│   ├── auth/                 # 密码哈希与 JWT
│   └── database/             # ORM 模型、Repository 与数据库会话
├── agent/
│   ├── llm/                  # DeepSeek 客户端
│   ├── tools/                # MES 和知识库工具
│   ├── sql/                  # SQL 生成、校验、执行与纠错
│   ├── analytics/            # 数据分析与图表生成
│   └── workflow/             # LangGraph 节点、执行器、持久化及流式输出
├── knowledge/
│   ├── documents/            # 设备、报警、SOP、质量等示例文档
│   ├── ingestion/            # 文档加载、分块与向量化
│   ├── retrieval/            # 向量检索与 RAG
│   └── management/           # 知识文档管理
├── alembic/                  # 数据库迁移
├── scripts/                  # 数据、账号、知识库和工作流初始化脚本
├── tests/                    # API、Agent、SQL、知识库与工作流测试
├── data/mock/                # JSON 演示数据
├── docs/architecture/        # 各阶段架构记录
├── docker-compose.yml        # PostgreSQL + pgvector 开发容器
└── .env.example              # 部分后端配置示例
```

主要业务表为 `machines`、`machine_alarms`、`work_orders`、`materials`、`production_records`；知识库使用 `knowledge_documents`、`knowledge_chunks`；认证使用 `auth_users`。工作流另有 Checkpoint、线程归属及审批审计表。

## 3. 本地启动

以下命令默认在项目根目录执行，前端命令需先进入 `frontend`。示例使用 Windows PowerShell。

### 3.1 环境与依赖

- Python 建议使用 3.12，与仓库当前本地虚拟环境版本一致。
- Node.js 建议使用 22 LTS，并安装 npm。
- Docker Desktop / Docker Compose，或自行提供带 pgvector 的 PostgreSQL。
- AI 功能需要可用的 DeepSeek API Key；首次使用 BGE 模型需要下载模型文件。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

仓库当前没有 `requirements.txt` 或 Python 依赖锁定文件，`pyproject.toml` 仅包含 Ruff 配置。以下是根据源码导入整理的安装起点，尚非锁定并验证的完整版本集合：

```powershell
python -m pip install "fastapi>=0.121" "uvicorn[standard]" "pydantic>=2" pydantic-settings "sqlalchemy>=2" alembic "psycopg[binary,pool]" pgvector python-dotenv openai langgraph langgraph-checkpoint-postgres sqlglot sentence-transformers pypdf PyJWT "pwdlib[argon2]" pytest httpx
```

FastAPI 接口使用 `Depends(..., scope="request")`，需要支持该参数的版本。安装并验证后，可用 `python -m pip freeze > requirements.local.txt` 保存本机依赖版本。

### 3.2 后端环境配置

首次配置时复制模板；已有 `.env` 时直接编辑，避免覆盖：

```powershell
Copy-Item .env.example .env
```

补全 `.env`，下列数据库密码与当前 Compose 开发配置一致：

```dotenv
APP_NAME=ManuAgent
APP_ENV=development
APP_DEBUG=true
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=manu
DATABASE_PASSWORD=dev_password
DATABASE_NAME=manu_agent

LANGGRAPH_CHECKPOINT_DSN=postgresql://manu:dev_password@localhost:5432/manu_agent

DEEPSEEK_API_KEY=替换为自己的API密钥
DEEPSEEK_MODEL=deepseek-flash

WORKFLOW_JWT_SECRET=替换为至少32个字符的随机密钥
WORKFLOW_JWT_ISSUER=manu-agent
WORKFLOW_JWT_AUDIENCE=manu-agent-web
WORKFLOW_ACCESS_TOKEN_MINUTES=30

RAG_TOP_K=5
RAG_MAX_TOP_K=10
RAG_MIN_SCORE=0.50
```

`.env.example` 的数据库密码为占位符 `your_password`，需与 Compose 的 `dev_password` 对齐，或同步修改两处配置。模型名称来自当前代码默认值，需确认自己的账户支持所配置模型。

### 3.3 启动数据库并初始化表

```powershell
docker compose up -d postgres
docker compose ps
```

等待数据库健康检查通过后执行：

```powershell
python -m alembic upgrade head
python -m scripts.init_auth_tables
python -m scripts.init_workflow_checkpoint
python -m scripts.init_workflow_threads
```

Alembic 创建 MES 和知识库表，其他脚本创建用户表、Checkpoint 和线程归属表。自行部署 PostgreSQL 时，也需要安装并启用 `vector` 扩展。

如需调试审批和恢复模块，再执行：

```powershell
python -m scripts.init_approval_tables
```

### 3.4 导入演示数据并创建账号

```powershell
python -m scripts.generate_mock_data
python -m scripts.seed_demo_data
python -m scripts.create_auth_user --username admin --role workflow_approver
```

创建账号时交互输入两次密码，密码至少 12 位。没有内置通用账号；普通角色可以使用 `--role viewer` 创建。

演示数据涵盖设备、物料、生产记录、报警和工单，预设 MC-003 等异常设备及低库存场景。导入脚本遇到已有演示编码会停止，避免重复插入，不会自动清库覆盖。

### 3.5 导入知识库

```powershell
python -m scripts.ingest_knowledge
```

脚本扫描 `knowledge/documents/`，将文档分块、向量化后写入数据库。首次下载 BGE 模型可能耗时较长。只调试 MES 接口可以跳过，使用知识问答前应完成入库。

### 3.6 启动后端

保持虚拟环境激活，在项目根目录执行：

```powershell
python -m uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

- 接口文档：<http://127.0.0.1:8000/docs>
- 服务健康检查：<http://127.0.0.1:8000/health>
- 数据库健康检查：<http://127.0.0.1:8000/health/db>

### 3.7 启动前端

另开终端：

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

访问 <http://localhost:5173>，使用已创建的账号登录。已有 `.env.local` 时无需再次复制。

Vite 将 `/api`、`/health` 默认代理至 `http://127.0.0.1:8000`。后端地址不同时，在 `frontend/.env.local` 设置：

```dotenv
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
```

后续启动只需运行数据库、后端和前端，无需重复导入演示数据或创建账号。

## 4. 主要 API

| 接口 | 用途 |
| --- | --- |
| `GET /health`、`GET /health/db` | 服务与数据库健康检查 |
| `POST /api/v1/auth/login`、`GET /api/v1/auth/me` | 登录与当前用户 |
| `/api/v1/machines` | 设备管理 |
| `/api/v1/alarms` | 报警管理 |
| `/api/v1/work-orders` | 工单管理 |
| `/api/v1/materials` | 库存管理 |
| `/api/v1/production-records` | 生产记录 |
| `POST /api/v1/agent/chat` | 普通 Agent 对话 |
| `POST /api/v1/agent/chat/stream` | NDJSON 流式对话 |
| `POST /api/v1/agent/bi/query` | 自然语言 BI 查询 |
| `POST /api/v1/knowledge/query` | 知识库问答 |
| `GET /api/v1/knowledge/documents`、`GET /api/v1/knowledge/status` | 文档列表与知识库状态 |
| `POST /api/v1/workflow/chat` | 工作流执行，需要 Bearer Token |
| `POST /api/v1/workflow/chat/stream` | SSE 工作流事件流，需要 Bearer Token |

字段、子路径与具体 HTTP 方法以 Swagger 为准。例如 BI 请求体：

```json
{
  "question": "查询报警次数最多的5台设备"
}
```

BI 返回只读 SQL、查询数据、分析结论、图表规格与 `echarts_option`，表格降级时 `echarts_option` 为 `null`。

## 5. 测试与构建

后端测试默认从 `tests/` 收集：

```powershell
python -m pytest -v
```

按模块运行：

```powershell
python -m pytest tests/api tests/agent tests/sql tests/knowledge -v
python -m pytest tests/workflow -v
```

测试涵盖 MES API、认证、工具调用、流式对话、BI、SQL 校验、知识检索、工作流编排、Checkpoint 和审批。部分 API 测试使用 SQLite 内存库，部分工作流集成测试需要真实 PostgreSQL，不能将所有测试都视为无外部依赖。

PostgreSQL 审批集成测试使用独立数据库，通过 `.env` 配置 `TEST_APPROVAL_DSN`。数据库名称应以 `_test` 结尾，初始化脚本不会代为创建数据库：

```dotenv
TEST_APPROVAL_DSN=postgresql://manu:dev_password@localhost:5432/manu_agent_test
```

```powershell
python -m scripts.init_workflow_approvals
python -m scripts.init_workflow_threads --test
```

`scripts/test_*.py` 是手工验证脚本，其中部分调用真实模型或数据库，不在默认测试收集目录中。

前端构建命令在 `frontend/` 执行：

```powershell
npm run build
npm run preview
```

构建产物为 `frontend/dist/`。开发代理只属于 Vite 开发服务器；部署时需用网关转发 API，或设置 `VITE_API_BASE_URL` 并在后端配置跨域策略。BrowserRouter 静态部署需要将业务路径回退到 `index.html`，以支持当前页面刷新。

## 6. 常见问题

| 现象 | 检查方向 |
| --- | --- |
| 数据库连接失败 | 容器状态、5432 端口、`.env` 与 Compose 的账号密码 |
| 表不存在 | Alembic 迁移，以及用户、Checkpoint、线程、审批表初始化 |
| 登录报 JWT 配置错误 | 至少 32 字符的密钥，以及 issuer、audience 配置 |
| 刷新后登录失效 | 新配置下重新登录一次；sessionStorage 保留当前标签页会话，JWT 过期或 401 会清除状态 |
| AI 请求失败 | DeepSeek Key、模型可用性和外部网络；基础 MES 接口本身不调用模型 |
| 知识问答没有来源 | 知识入库状态、BGE 模型下载及检索阈值 |
| 工作流首次执行失败 | `LANGGRAPH_CHECKPOINT_DSN`、Checkpoint 和 `workflow_threads` 表 |
| 前端构建失败 | 先处理 TypeScript 报错，构建会先类型检查，再执行 Vite 打包 |

历史设计见 [架构文档目录](docs/architecture/)。各阶段文档记录设计演进，当前可用能力以入口路由、实际实现与测试为准。
