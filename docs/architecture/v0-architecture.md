             HTTP
              ↓
        ┌───────────┐
        │ FastAPI   │
        └─────┬─────┘
              ↓
        ┌───────────┐
        │MES Service│
        └─────┬─────┘
              ↓
        ┌───────────┐
        │Repository │
        └─────┬─────┘
              ↓
        ┌───────────┐
        │SQLAlchemy │
        └─────┬─────┘
              ↓
        ┌───────────┐
        │PostgreSQL │
        └───────────┘


<!-- 最终 -->


                            ┌──── FastAPI ──── Web
                    │
PostgreSQL ← Repository ← MES Service
                    │
                    └──── Agent Tools ─── LangGraph


V1  Tool Agent
        ↓
V2  Enterprise RAG
        ↓
V3  SQL Agent / BI Agent
        ↓
V4  LangGraph Workflow Agent
        ↓
V5  Memory + Human-in-the-loop
        ↓
V6  Evaluation + Observability
        ↓
V7  Production Deployment