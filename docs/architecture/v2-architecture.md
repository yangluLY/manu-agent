# ManuAgent V2 Architecture

> 版本：V2  
> 主题：RAG 企业知识库 + MES Agent 集成  
> 文档状态：当前 V2 实现说明

---

## 1. V2 目标

ManuAgent V2 在 V1 的 MES Agent 能力基础上，引入企业知识库 RAG（Retrieval-Augmented Generation），使 Agent 不仅能够查询实时生产业务数据，还能够结合设备说明书、报警处理手册、维修 SOP、生产 SOP 和质量规范等企业知识进行回答。

V2 的核心目标：

- 支持企业知识文档导入
- 支持 Markdown / TXT / PDF 文档解析
- 支持文档切片与向量化
- 使用 PostgreSQL + pgvector 存储向量
- 使用 BAAI/bge-small-zh-v1.5 生成中文 Embedding
- 支持 TopK 向量检索与 Similarity Threshold
- 支持 Metadata Filter
- 支持独立 RAG 问答 API
- 支持知识库文档管理 API
- 将知识检索能力接入 ManuAgent Tool System
- 支持 MES 实时数据 + 企业知识库联合推理
- 建立 Retrieval Evaluation 评测机制

---

## 2. V2 总体架构

```text
                         ┌─────────────────────┐
                         │        User         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI API      │
                         └──────────┬──────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
          /api/v1/agent/chat            /api/v1/knowledge/query
                     │                             │
                     ▼                             ▼
              ┌─────────────┐               ┌─────────────┐
              │  ManuAgent  │               │ RAGService  │
              └──────┬──────┘               └──────┬──────┘
                     │                             │
          ┌──────────┼──────────┐                  │
          │          │          │                  │
          ▼          ▼          ▼                  ▼
     MES Tools   Knowledge   DeepSeek         KnowledgeRetriever
                  Tool                            │
                    │                             │
                    ▼                             ▼
             KnowledgeRetriever             BGE Embedding
                    │                             │
                    ▼                             ▼
              BGE Embedding                PostgreSQL
                    │                         + pgvector
                    ▼
              PostgreSQL
               + pgvector
```

V2 同时保留两种使用方式：

1. **独立 RAG API**
   - 面向企业知识问答
   - 通过 `RAGService` 检索知识并调用 DeepSeek 生成答案

2. **Agent + RAG**
   - 面向真实生产运营问题
   - Agent 根据问题决定调用 MES Tool、Knowledge Tool，或两者同时调用

---

## 3. V2 目录结构

```text
manu-agent/
│
├── agent/
│   ├── agent.py
│   ├── executor.py
│   ├── factory.py
│   ├── registry.py
│   │
│   ├── llm/
│   │   └── deepseek_client.py
│   │
│   ├── prompts/
│   │   └── system_prompt.py
│   │
│   └── tools/
│       ├── machine_tools.py
│       ├── alarm_tools.py
│       ├── inventory_tools.py
│       ├── work_order_tools.py
│       ├── production_tools.py
│       ├── knowledge_tools.py
│       ├── serializers.py
│       └── types.py
│
├── apps/
│   └── api/
│       └── app/
│           ├── routers/
│           │   └── knowledge.py
│           └── schemas/
│               └── knowledge.py
│
├── knowledge/
│   ├── documents/
│   │   ├── alarm/
│   │   ├── equipment/
│   │   ├── sop/
│   │   └── quality/
│   │
│   ├── ingestion/
│   │   ├── loaders.py
│   │   ├── splitter.py
│   │   ├── embedder.py
│   │   └── pipeline.py
│   │
│   ├── retrieval/
│   │   ├── config.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── rag_service.py
│   │
│   └── management/
│       └── service.py
│
├── services/
│   └── database/
│       ├── models/
│       │   ├── knowledge_document.py
│       │   └── knowledge_chunk.py
│       └── repositories/
│           └── knowledge_repository.py
│
├── scripts/
│   ├── ingest_knowledge.py
│   ├── test_loader.py
│   ├── test_splitter.py
│   ├── test_embedder.py
│   ├── test_retriever.py
│   ├── test_rag.py
│   └── evaluate_retrieval.py
│
└── tests/
    └── knowledge/
        ├── test_retriever.py
        └── evaluation_cases.json
```

---

## 4. Offline RAG Pipeline

Offline Pipeline 负责把企业知识文档转换成可检索的向量数据。

```text
Knowledge Documents
        │
        ▼
 DocumentLoader
        │
        ▼
 LoadedDocument
        │
        ▼
   TextSplitter
        │
        ▼
  DocumentChunk[]
        │
        ▼
     Embedder
        │
        ▼
  512-dim Vector
        │
        ▼
KnowledgeRepository
        │
        ▼
PostgreSQL + pgvector
```

### 4.1 DocumentLoader

位置：

```text
knowledge/ingestion/loaders.py
```

职责：

- 读取企业知识文件
- 支持 `.md`
- 支持 `.txt`
- 支持 `.pdf`
- 统一输出 `LoadedDocument`
- 生成文件 metadata

典型 metadata：

```json
{
  "source": "knowledge/documents/alarm/cnc_alarm_manual.md",
  "file_name": "cnc_alarm_manual.md",
  "file_type": "md",
  "category": "alarm"
}
```

---

## 5. Text Splitter

位置：

```text
knowledge/ingestion/splitter.py
```

当前默认配置：

```text
chunk_size = 500
chunk_overlap = 100
```

切分策略：

- 优先按自然段落切分
- 优先保留完整中文句子
- 支持段落、换行、句号、问号、感叹号、分号等边界
- 找不到自然边界时按字符长度切分
- 相邻 Chunk 保留 overlap

目的：

- 避免整份大文档直接生成一个向量
- 提高语义检索精度
- 减少知识边界切断带来的信息损失

---

## 6. Embedding

位置：

```text
knowledge/ingestion/embedder.py
```

当前使用模型：

```text
BAAI/bge-small-zh-v1.5
```

模型用途：

```text
知识 Chunk
   ↓
Embedding Model
   ↓
512 维向量
```

以及：

```text
用户问题
   ↓
Embedding Model
   ↓
512 维 Query Vector
```

当前数据库向量字段：

```python
Vector(512)
```

Embedding 与 LLM 职责不同：

```text
BGE
负责：
文本向量化
语义检索

DeepSeek
负责：
推理
Tool Calling
自然语言生成
```

---

## 7. Ingestion Pipeline

位置：

```text
knowledge/ingestion/pipeline.py
```

核心职责：

```text
Loader
  ↓
Splitter
  ↓
Embedder
  ↓
KnowledgeRepository
  ↓
PostgreSQL
```

入口脚本：

```bash
python scripts/ingest_knowledge.py
```

重复导入策略：

```text
同一路径文档已存在
        ↓
保留 knowledge_documents
        ↓
删除旧 knowledge_chunks
        ↓
重新切片
        ↓
重新生成 embedding
        ↓
插入新 chunks
```

这样可以避免重复导入产生重复知识。

---

## 8. PostgreSQL + pgvector

V2 继续使用 PostgreSQL，不额外引入独立 Vector Database。

Docker Image：

```text
pgvector/pgvector:pg16
```

数据库扩展：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 8.1 knowledge_documents

保存原始知识文档信息。

主要字段：

```text
id
name
file_path
file_type
category
source
created_at
updated_at
```

### 8.2 knowledge_chunks

保存文档切片与 Embedding。

主要字段：

```text
id
document_id
content
chunk_index
metadata
embedding VECTOR(512)
created_at
```

关系：

```text
knowledge_documents
        │
        │ 1 : N
        ▼
knowledge_chunks
```

---

## 9. Online Retrieval Pipeline

Online Pipeline 负责根据用户问题检索最相关的企业知识。

```text
User Query
    │
    ▼
embed_query()
    │
    ▼
512-dim Query Vector
    │
    ▼
VectorStore
    │
    ▼
pgvector Cosine Search
    │
    ▼
Top K Chunks
    │
    ▼
KnowledgeRetriever
```

---

## 10. VectorStore

位置：

```text
knowledge/retrieval/vector_store.py
```

核心能力：

- Cosine Distance
- TopK 检索
- Similarity Threshold
- Category Filter
- File Type Filter
- Document Filter
- JSONB Metadata Filter

相似度换算：

```text
score = 1 - cosine_distance
```

因此：

```text
score 越大
→ 语义越相关
```

---

## 11. Retrieval Quality

位置：

```text
knowledge/retrieval/config.py
```

环境变量示例：

```env
RAG_TOP_K=5
RAG_MAX_TOP_K=10
RAG_MIN_SCORE=0.50
```

其中：

```text
RAG_TOP_K
默认检索数量

RAG_MAX_TOP_K
允许的最大检索数量

RAG_MIN_SCORE
最低相似度阈值
```

当结果低于 Threshold 时：

```text
低相关 Chunk
     ↓
被过滤
     ↓
Retriever 返回 []
```

从而避免知识库没有答案时仍然强行返回无关内容。

---

## 12. RAGService

位置：

```text
knowledge/retrieval/rag_service.py
```

完整流程：

```text
Question
   ↓
KnowledgeRetriever
   ↓
Top K Chunks
   ↓
Build Context
   ↓
Build RAG Instructions
   ↓
DeepSeekClient.create_response()
   ↓
Answer + Sources
```

如果 Retriever 没有返回可靠知识：

```text
results = []
```

则：

- 不调用 DeepSeek
- 直接返回知识库资料不足

这样可以降低模型在企业知识问答中的幻觉风险。

---

## 13. Knowledge API

V2 提供独立知识库 API。

### 13.1 RAG Query

```http
POST /api/v1/knowledge/query
```

请求：

```json
{
  "question": "CNC主轴温度过高应该怎么处理？",
  "top_k": 3,
  "category": "alarm"
}
```

返回：

```json
{
  "answer": "根据企业知识库中的报警处理手册……",
  "sources": [
    {
      "chunk_id": 1,
      "document_id": 1,
      "document_name": "cnc_alarm_manual",
      "chunk_index": 0,
      "score": 0.82,
      "content": "..."
    }
  ]
}
```

### 13.2 文档列表

```http
GET /api/v1/knowledge/documents
```

### 13.3 删除知识文档

```http
DELETE /api/v1/knowledge/documents/{document_id}
```

当前策略：

- 删除数据库索引
- 删除 `knowledge_documents`
- 级联删除对应 `knowledge_chunks`
- 不删除本地原始知识文件

### 13.4 重新导入

```http
POST /api/v1/knowledge/documents/{document_id}/reingest
```

### 13.5 Knowledge Status

```http
GET /api/v1/knowledge/status
```

返回统计信息：

```text
documents
chunks
embedded_chunks
categories
```

---

## 14. Agent + RAG

V2 最重要的升级是将 RAG 接入 ManuAgent Tool System。

新增：

```text
agent/tools/knowledge_tools.py
```

核心 Tool：

```text
search_knowledge
```

调用链：

```text
DeepSeek
    │
    ▼
search_knowledge
    │
    ▼
KnowledgeTools
    │
    ▼
KnowledgeRetriever
    │
    ▼
BGE + pgvector
    │
    ▼
Top K Knowledge Chunks
    │
    ▼
ToolResult
    │
    ▼
ManuAgent
    │
    ▼
DeepSeek 综合回答
```

Knowledge Tool 不调用 `RAGService`。

原因：

```text
Agent 本身已经有 DeepSeek
```

如果 Knowledge Tool 再调用 RAGService，会产生额外 LLM 调用。

因此 Agent 模式采用：

```text
Knowledge Tool
    ↓
只负责 Retrieval
```

最终语言生成仍由 Agent 自己完成。

---

## 15. MES + RAG 联合推理

V1：

```text
User
 ↓
ManuAgent
 ↓
MES Tools
 ↓
DeepSeek
```

V2：

```text
User
 ↓
ManuAgent
 │
 ├── Machine Tool
 ├── Alarm Tool
 ├── Inventory Tool
 ├── WorkOrder Tool
 ├── Production Tool
 │
 └── Knowledge Search Tool
          ↓
     KnowledgeRetriever
```

典型问题：

```text
MC-003 当前有哪些报警？这些报警应该怎么处理？
```

执行流程：

```text
1. get_machine_alarms("MC-003")
        ↓
   获取真实 MES 报警

2. 根据实际报警代码构造知识查询

3. search_knowledge(...)
        ↓
   检索企业报警处理手册

4. DeepSeek 综合：
   实时 MES 数据
   +
   企业知识
        ↓
   最终回答
```

这样 Agent 能够区分：

```text
实时事实
+
企业知识
```

---

## 16. Agent Tool Architecture

当前 Tool 体系：

```text
ToolRegistry
    │
    ├── list_machines
    ├── get_machine_by_code
    ├── get_machine_detail
    ├── get_machine_status
    ├── get_machine_alarms
    ├── get_machine_production_stats
    ├── get_low_stock_materials
    ├── get_machine_work_orders
    ├── create_work_order
    └── search_knowledge
```

Agent 执行链：

```text
DeepSeek Function Call
       ↓
ManuAgent
       ↓
ToolExecutor
       ↓
ToolRegistry
       ↓
Python Handler
       ↓
ToolResult
       ↓
Function Call Output
       ↓
DeepSeek
```

所有 Tool 统一返回：

```text
ToolResult
```

成功：

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

失败：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "...",
    "message": "...",
    "details": {}
  }
}
```

---

## 17. System Prompt 策略

V2 System Prompt 增加企业知识库使用规则。

核心原则：

```text
实时 MES 数据
→ 必须调用 MES Tool

设备故障 / 报警处理 / SOP / 企业规范
→ 调用 search_knowledge

同时包含实时数据和企业知识
→ 两类 Tool 都调用
```

并要求：

- 不猜测实时生产数据
- 不把模型自身知识描述成企业内部规定
- 不编造安全阈值
- 不编造维修步骤
- 不编造报警代码
- 知识库无可靠结果时明确说明资料不足

---

## 18. Retrieval Evaluation

V2 建立 Retrieval Evaluation，用于量化检索效果。

文件：

```text
tests/knowledge/evaluation_cases.json
scripts/evaluate_retrieval.py
```

评测数据包含：

```text
Positive Cases
Negative Cases
Hard Negative Cases
```

### 18.1 Positive Case

例：

```text
Query:
伺服过载报警一般有哪些原因？

Expected:
servo_overload_alarm
```

### 18.2 Negative Case

例：

```text
Query:
公司的差旅报销标准是多少？

Expected:
不应返回知识结果
```

### 18.3 核心指标

```text
Hit@K
Top1 Accuracy
MRR
Negative Rejection Rate
```

含义：

```text
Hit@K
正确文档是否出现在 TopK

Top1 Accuracy
第一名是否为正确文档

MRR
正确文档排名质量

Negative Rejection Rate
知识库没有答案时能否正确拒绝
```

---

## 19. Similarity Threshold Evaluation

Evaluation 会扫描多个 Threshold：

```text
0.35
0.40
0.45
0.50
0.55
0.60
0.65
0.70
```

目标不是单纯最大化 Recall，而是在：

```text
Positive Retrieval
+
Negative Rejection
```

之间取得平衡。

最终 `RAG_MIN_SCORE` 应基于实际 Evaluation 结果确定，而不是凭经验写死。

---

## 20. V2 技术栈

### Backend

```text
Python
FastAPI
SQLAlchemy
Alembic
Pydantic
```

### Database

```text
PostgreSQL 16
pgvector
```

### Embedding

```text
sentence-transformers
BAAI/bge-small-zh-v1.5
512 dimensions
```

### LLM

```text
DeepSeek
Responses API
```

### RAG

```text
Custom Document Loader
Custom Text Splitter
Custom Embedder Wrapper
Custom VectorStore
Custom Retriever
Custom RAGService
```

V2 核心 RAG Pipeline 暂未依赖 LangChain / LlamaIndex。

---

## 21. V2 关键设计原则

### 21.1 RAG 与 Agent 解耦

```text
KnowledgeRetriever
       ↑
       │
 ┌─────┴─────┐
 │           │
RAGService  Agent Tool
```

同一个 Retriever 同时服务：

- 独立 RAG API
- ManuAgent Tool

---

### 21.2 LLM 与 Embedding 解耦

```text
DeepSeek
→ 推理与回答

BGE
→ Embedding 与 Retrieval
```

---

### 21.3 Repository 不控制事务

数据库事务由 Pipeline / Service 控制。

目的：

- 避免导入一半留下脏数据
- 支持 rollback
- 支持文档级事务

---

### 21.4 Tool 不直接生成最终回答

```text
Tool
→ 获取事实

Agent
→ 综合事实并回答
```

这样 MES Tool、Knowledge Tool 都保持统一职责。

---

### 21.5 无知识结果不等于系统错误

```text
Retriever 正常执行
+
results = []
```

属于：

```text
success = true
```

只是表示当前企业知识库没有足够相关资料。

---

## 22. V2 数据流总结

### 文档导入

```text
Document
 ↓
Loader
 ↓
Splitter
 ↓
Embedding
 ↓
Repository
 ↓
pgvector
```

### 独立 RAG 问答

```text
Question
 ↓
Retriever
 ↓
TopK
 ↓
Context
 ↓
DeepSeek
 ↓
Answer
```

### Agent + RAG

```text
Question
 ↓
ManuAgent
 ↓
DeepSeek Tool Planning
 ↓
MES Tool / Knowledge Tool
 ↓
ToolResult
 ↓
DeepSeek
 ↓
Final Answer
```

---

## 23. Local Development

启动 PostgreSQL：

```bash
docker compose up -d
```

执行数据库迁移：

```bash
alembic upgrade head
```

导入企业知识：

```bash
python scripts/ingest_knowledge.py
```

测试 Retriever：

```bash
python scripts/test_retriever.py
```

测试 RAG：

```bash
python scripts/test_rag.py
```

执行 Retrieval Evaluation：

```bash
python scripts/evaluate_retrieval.py
```

启动 API：

```bash
uvicorn apps.api.app.main:app --reload
```

Swagger：

```text
http://127.0.0.1:8000/docs
```

---

## 24. V2 当前能力

V2 已实现：

```text
✅ PostgreSQL + pgvector
✅ Knowledge Document / Chunk Model
✅ Markdown / TXT / PDF Loader
✅ Text Splitter
✅ BGE Embedding
✅ Knowledge Ingestion Pipeline
✅ Vector Retrieval
✅ Similarity Threshold
✅ Metadata Filter
✅ TopK Configuration
✅ RAG Service
✅ Knowledge Query API
✅ Knowledge Management API
✅ Agent Knowledge Tool
✅ MES + RAG 联合 Tool Calling
✅ Retrieval Evaluation
```

---

## 25. 后续演进方向

V2 完成后可继续进入 V3：

```text
V3.1 Hybrid Retrieval
Vector Search + BM25

V3.2 Reranker
TopK Recall + Rerank

V3.3 Improved Chunking
Markdown-aware / Semantic Chunking

V3.4 Knowledge Versioning
文档版本、Hash、增量更新

V3.5 Async Ingestion
后台文档导入任务

V3.6 Observability
Agent Trace / Tool Trace / RAG Trace

V3.7 Structured Agent Output
统一返回 Answer / Sources / Recommendations

V3.8 Agent Evaluation
Tool Selection Accuracy
RAG Groundedness
Answer Quality
```

---

## 26. V2 Architecture Summary

ManuAgent V2 的核心不是单独增加一个 RAG Chatbot，而是在 V1 MES Agent 基础上增加企业知识能力：

```text
                   ManuAgent V2

                      User
                       │
                       ▼
                    Agent
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
     MES Data      Knowledge       DeepSeek
       Tools          Tool
         │             │
         ▼             ▼
   PostgreSQL     Retriever
                     │
                     ▼
                  pgvector
                     │
                     ▼
              Enterprise Knowledge
```

最终实现：

```text
实时生产业务数据
        +
企业设备 / 报警 / SOP / 质量知识
        +
LLM 推理
        ↓
智能制造生产运营 Agent
```
