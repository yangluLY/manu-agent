# manu-agent
Enterprise AI Agent for Manufacturing Production Operations
manu-agent/
│
├── apps/
│   ├── api/                 # FastAPI 后端
│   └── web/                 # React 前端
│
├── agent/
│   ├── graphs/              # Agent 工作流
│   ├── nodes/               # LangGraph Node
│   ├── tools/               # Agent 工具
│   ├── prompts/             # Prompt
│   └── memory/              # Agent Memory
│
├── knowledge/
│   ├── documents/           # SOP / 设备文档
│   ├── ingestion/           # 文档入库
│   └── retrieval/           # RAG
│
├── services/
│   ├── mes/                 # 模拟 MES 服务
│   ├── llm/                 # LLM
│   └── database/            # 数据库访问
│
├── data/
│   └── mock/                # 模拟制造数据
│
├── tests/
│
├── docker/
│
├── docs/
│   ├── architecture/
│   └── api/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
└── pyproject.toml
