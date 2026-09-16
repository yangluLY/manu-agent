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