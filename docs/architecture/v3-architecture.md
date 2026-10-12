## V3 — SQL Agent / BI Agent

V3 在 V1 Tool Agent 和 V2 Enterprise RAG 的基础上增加结构化数据分析能力，使 ManuAgent 可以通过自然语言查询 MES PostgreSQL 数据库，并自动完成 SQL 生成、安全校验、数据查询、结果分析和图表推荐。

### Architecture

```text
                        User
                          │
                          ▼
              POST /api/v1/analytics/query
                          │
                          ▼
                       BIAgent
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
        SQLPipeline   DataAnalyzer  ChartGenerator
             │
             ▼
       SchemaProvider
             │
             ▼
        SQLGenerator
             │
             ▼
        SQLValidator
             │
             ▼
        SQLExecutor
             │
             ▼
         PostgreSQL
             │
             │ Failed
             ▼
        SQLCorrector
             │
             └──────────→ Retry
```

### SQL Agent Pipeline

```text
Natural Language
      ↓
Schema Discovery
      ↓
Text-to-SQL
      ↓
SQL Validation
      ↓
Read-only Execution
      ↓
SQL Correction / Retry
      ↓
QueryResult
```

SQL Agent 不直接执行 LLM 输出。生成的 SQL 必须经过程序级安全校验，仅允许只读查询，并通过表白名单、只读事务、查询超时和最大结果行数等机制限制数据库访问。

### BI Pipeline

```text
User Question
      ↓
SQLPipeline
      ↓
QueryResult
      ├───────────────┐
      ↓               ↓
DataAnalyzer     ChartGenerator
      ↓               ↓
Business Insight   ChartSpec
      └───────┬───────┘
              ↓
          BI Response
```

DataAnalyzer 根据真实查询结果生成业务摘要、关键发现、建议和数据限制。

ChartGenerator 不直接生成图片，而是生成统一的 ChartSpec，目前支持：

`bar / line / pie / table`

后续前端可以将 ChartSpec 转换为 ECharts 配置进行可视化展示。

### V3 Modules

| Version | Capability | Status |
|---|---|---|
| V3.1 | Database Schema Discovery | ✅ |
| V3.2 | Text-to-SQL | ✅ |
| V3.3 | SQL Safety / Validator | ✅ |
| V3.4 | Read-only SQL Executor | ✅ |
| V3.5 | SQL Retry / Correction | ✅ |
| V3.6 | Data Analyst | ✅ |
| V3.7 | Chart Generator | ✅ |
| V3.8 | BI API | ✅ |

### BI API

```http
POST /api/v1/analytics/query
```

Request:

```json
{
  "question": "查询报警次数最多的5台设备"
}
```

Response:

```json
{
  "question": "查询报警次数最多的5台设备",
  "sql": "SELECT ...",
  "data": {
    "columns": [],
    "rows": [],
    "row_count": 0,
    "execution_time_ms": 0,
    "truncated": false
  },
  "analysis": {
    "summary": "",
    "key_findings": [],
    "recommendations": [],
    "limitations": []
  },
  "chart": {
    "type": "bar",
    "title": "",
    "data": []
  },
  "retry_count": 0
}
```

### V3 Safety

V3 对 SQL Agent 采用多层防护：

```text
LLM Prompt Constraint
        ↓
SQL AST Validator
        ↓
Table Allowlist
        ↓
Read-only Transaction
        ↓
Statement Timeout
        ↓
Maximum Result Rows
```

SQL Validation Error 不允许通过 Retry 绕过；只有数据库执行错误才允许进入 SQL Correction。

### Testing

V3 包含单元测试、SQL Pipeline 集成测试以及 Analytics API 测试。

```bash
python -m pytest tests/integration/test_v3_bi_pipeline.py -v

python -m pytest tests/api/test_analytics.py -v

python -m pytest -v
```

真实 LLM 调用仅用于开发和 Smoke Test，自动化测试使用 Fake LLM 保证测试稳定、可重复并避免外部 API 依赖。

### Version Evolution

```text
V1 Tool Agent
      ↓
MES Tool Calling

V2 Enterprise RAG
      ↓
Enterprise Knowledge

V3 SQL / BI Agent
      ↓
Structured Data Intelligence

V4 LangGraph
      ↓
Workflow Orchestration
```

V4 将基于 V1、V2、V3 已有能力，引入 Router、Planner、State、Conditional Edge、Retry 和 Checkpoint，对 Tool、RAG 和 SQL Agent 进行统一工作流编排。