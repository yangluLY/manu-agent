
## V4：LangGraph Workflow Agent

ManuAgent V4 基于 LangGraph，将已有 MES Agent、
RAG Agent 和 SQL/BI Agent 组织为可编排的工作流。

### 核心功能

- Router：自动识别业务请求类型
- Planner：生成简单或多步骤执行计划
- State：维护工作流执行上下文
- Conditional Edge：根据路由及审批决定选择执行路径
- Step Executor：统一执行 MES、RAG 和 BI 步骤
- RetryPolicy：处理适合重试的瞬时故障
- Checkpoint：PostgreSQL 工作流持久化
- Human-in-the-Loop：人工审批、中断和恢复
- Secure Approval：审批角色校验、数据库行锁及审计
- Workflow History：查询线程状态和历史 Checkpoint
- SSE Streaming：流式返回工作流执行事件
- JWT Authentication：用户登录、身份认证和接口保护

### 架构

```text
React + TypeScript
        |
FastAPI + JWT
        |
LangGraph Workflow
        |
Router → Planner
        |
Approval Gate
        |
Step Executor
        |
MES / RAG / BI Agents
        |
PostgreSQL + pgvector
        |
Response Mapper
        |
JSON / SSE → React
```

详细设计：

[查看 V4 架构文档](docs/v4-architecture.md)

### Workflow API

| Method | Path | Description |
| --- | --- | --- |
| POST | /api/v1/workflow/chat | 执行普通工作流 |
| POST | /api/v1/workflow/chat/stream | SSE 流式执行 |
| POST | /api/v1/workflow/chat/approval | 创建审批工作流 |
| GET | /api/v1/workflow/{thread_id} | 查询工作流状态 |
| GET | /api/v1/workflow/{thread_id}/history | 查询 Checkpoint 历史 |
| GET | /api/v1/workflow/{thread_id}/approval | 查询待审批状态 |
| POST | /api/v1/workflow/{thread_id}/resume | 审批并恢复工作流 |

### 身份认证

| Method | Path | Description |
| --- | --- | --- |
| POST | /api/v1/auth/login | 用户登录 |
| GET | /api/v1/auth/me | 获取当前用户 |

受保护的接口要求：

Authorization: Bearer <access_token>

### 测试

```bash
# Workflow 单元与集成测试
python -m pytest tests/workflow/ -v -rs

# FastAPI 接口测试
python -m pytest tests/api/ -v

# 全量测试
python -m pytest tests/ -v
```

PostgreSQL 集成测试使用独立的 TEST_APPROVAL_DSN，
避免影响正式 MES 数据。

### V4 测试报告

[查看 V4 测试验收报告](docs/v4-test-report.md)

### 版本路线

| 版本 | 目标 |
| --- | --- |
| V0 | MES 基础后端与数据模型 |
| V1 | MES Tool Calling Agent |
| V2 | 企业知识库 RAG |
| V3 | SQL/BI Agent |
| V4 | LangGraph Workflow、Checkpoint、Approval、SSE、JWT |
| V4.9 | Evaluation & Observability |
| V5 | 进一步完善企业级部署、安全和多 Agent 协作 |
```

这里特别说明一下：Markdown 代码块中为了展示完整 README 章节，部分位置使用了嵌套代码围栏。实际复制到 README 时，正常保留 Markdown 标题、表格和代码块即可。

此外，如果你的根目录 README 已经包含完整 Technology Stack，直接补充 `LangGraph`、`PostgresSaver`、`PyJWT`、`Argon2`、`Axios` 和 `SSE`，不要再创建重复的技术栈章节。

---

## 四、Step 3：新增 `docs/v4-test-report.md`

建议把“执行过什么测试”和“实际通过结果”记录下来。

这是面试时很有用的一份工程证据，但不要虚构测试数量、覆盖率或通过率。

文件：`docs/v4-test-report.md`

<CodeBlock language="markdown" editable>
# ManuAgent V4 测试验收报告

## 1. 测试目标

验证 ManuAgent V4 的 LangGraph 工作流编排、
HTTP API、JWT 认证、SSE 输出、Checkpoint
持久化及人工审批功能。

## 2. 测试环境

- Python 虚拟环境：.venv
- 测试框架：pytest
- API 框架：FastAPI TestClient
- 关系数据库：PostgreSQL / SQLite
- 工作流持久化：PostgresSaver
- 审批存储：PostgreSQL
- LLM：Mock LLM
- MES 执行器：Mock Step Runner

PostgreSQL 集成测试使用独立测试数据库。

## 3. 测试范围

| 模块 | 测试内容 |
| --- | --- |
| Router | 请求分类与路由 |
| Planner | 简单和复杂执行计划 |
| Step Executor | 步骤执行和结果记录 |
| Retry | 安全重试及失败处理 |
| Response Mapper | 统一 WorkflowResponse |
| REST API | 参数校验、执行结果、异常处理 |
| SSE | 流式事件、顺序、错误输出 |
| JWT | 认证与接口保护 |
| Thread Ownership | 线程归属和访问控制 |
| Approval | 通过、拒绝、重复审批、权限 |
| Audit | 审批审计记录 |
| Checkpoint | 持久化与实例重建后恢复 |

## 4. 关键验收场景

### JWT

- 未认证请求返回 401
- 已认证请求可以访问授权接口
- 普通用户不能执行需审批权限的操作

### Workflow

- 请求经过 Router / Planner / Executor
- 返回统一 WorkflowResponse
- 执行失败可记录结构化错误

### SSE

- 输出 workflow_started
- 输出 route_completed
- 输出 step_completed
- 输出 workflow_completed
- 失败时输出相应错误事件

### Approval

- 审批通过后恢复执行
- 审批拒绝时不执行 MES 步骤
- 重复审批被阻止
- 无审批角色被拒绝
- 审计表写入审批决定
- 并发审批只成功处理一次

### PostgreSQL Checkpoint

- 暂停后保存工作流状态
- 关闭连接并重建 Workflow 实例
- 通过原 thread_id 找回暂停状态
- 使用 Command(resume=...) 继续执行

## 5. 执行命令

```bash
python -m pytest tests/api/ -v
python -m pytest tests/workflow/ -v -rs
python -m pytest tests/ -v -ra
```

前端构建：

```bash
cd frontend
npm run build
```

## 6. 本次执行结果

执行日期：待填写

| 测试范围 | Passed | Failed | Skipped |
| --- | --- | --- | --- |
| API | 待填写 | 待填写 | 待填写 |
| Workflow | 待填写 | 待填写 | 待填写 |
| 全量测试 | 待填写 | 待填写 | 待填写 |

注意：

- SKIPPED 不等于 PASSED。
- Mock Workflow 测试不代表真实 DeepSeek 端到端测试。
- 实例重建测试不完全等于跨操作系统进程恢复测试。

## 7. 已知风险

1. SSE 断连和取消传播仍需深入测试。
2. 审批与 Checkpoint 之间不具备完全原子的事务保证。
3. MES 写操作仍需独立的授权与幂等控制。
4. JWT 撤销和刷新机制需要后续完善。
5. 生产部署、性能测试及故障注入需要进一步实施。

## 8. 后续计划

V4.9：

- Trace 链路追踪
- Workflow 延迟与错误指标
- Router / Planner Evaluation
- SQL / RAG 质量评估
- Token 成本分析
```

这里的执行结果表建议你在最终回归测试后填写真实数字。

---

## 五、Step 4：最终检查

执行以下命令：

```bash
# 1. API 测试
python -m pytest tests/api/ -v

# 2. LangGraph 测试
python -m pytest tests/workflow/ -v -rs

# 3. 全项目测试
python -m pytest tests/ -v -ra
```

再验证前端：

```bash
cd frontend
npm run build
```

之后检查三个文件是否存在：

```text
README.md
docs/v4-architecture.md
docs/v4-test-report.md
```

### V4 完成标准

{@body const checks=["docs/v4-architecture.md 已建立","README 已补充 V4 架构和 API","docs/v4-test-report.md 已记录真实测试结果","Workflow / API 全量测试通过","PostgreSQL 审批测试无意外 SKIPPED","PostgreSQL Checkpoint 恢复测试通过","前端 npm run build 通过","已知限制和 V4.9 Roadmap 已记录"]}
{@body const [done,setDone]=DIL.useState([])}
<box border radius="xl" padding={3} gap={3}>
  <row align="center" justify="between">
    **ManuAgent V4.8.4.4 验收**
    <text color="secondary" tabularNums>{done.length}/{checks.length}</text>
  </row>
  <box background="surface-tertiary" height="6px" radius="full" clip>
    <box background="rgba(48,119,206,0.9)" width={`${done.length/checks.length*100}%`} height="100%" radius="full"/>
  </box>
  {#each checks as check,i}
    <checkbox key={i} checked={done.includes(i)} onChange={v=>setDone(s=>v?[...s,i]:s.filter(x=>x!==i))}>{check}</checkbox>
  {/each}
  <button block disabled={done.length!==checks.length} onClick={()=>GenUI.issueNewTurn("ManuAgent V4.8.4.4 的 Architecture、README、测试验收报告已完成，全部回归测试通过。开始 V4.9 Evaluation & Observability，请先规划 V4.9 的子版本，然后从 V4.9.1 Trace 开始逐文件开发。")}>
    V4 完成，进入 V4.9 <icon name="arrow-right" inline/>
  </button>
</box>

## 六、V4 完成后，你的项目在面试中怎么介绍？

可以这样说：

> ManuAgent 是我基于智能制造 MES 业务场景构建的 AI Agent 项目。前期实现了 MES Tool Calling、企业知识库 RAG 和 SQL/BI Agent，V4 则使用 LangGraph 将这些能力整合成可编排的工作流。
>
> 其中我重点实现了 Router、Planner、状态管理、条件分支、步骤执行、异常重试，以及基于 PostgreSQL Checkpoint 的持久化和人工审批恢复机制。同时使用 FastAPI 提供 REST 和 SSE 接口，React 展示实时执行过程，并通过 JWT、工作流归属校验、审批角色和 PostgreSQL 行锁控制访问及重复审批。
>
> 项目目前完成了核心模块测试、HTTP 集成测试和 PostgreSQL 审批恢复测试。接下来会重点完善 Agent Evaluation、链路追踪和可观测性，以及生产环境的可靠性和权限控制。

这段介绍既能说明你从前端工程师逐步扩展到 AI Agent 工程的技术路线，也不会把仍在完善的功能说成已经生产上线。

**下一阶段建议正式进入 V4.9：Evaluation & Observability。** 从 `V4.9.1 Workflow Trace` 开始，为每次 Agent 执行建立可追踪的 `trace_id`，记录 Router 决策、Planner 计划、步骤耗时、错误、Token 使用量，为后续的评估面板提供数据基础。