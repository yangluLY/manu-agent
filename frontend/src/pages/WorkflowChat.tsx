
import { useState } from "react";
import { useAuth } from '../context/AuthContext';
import { useWorkflow } from "../hooks/useWorkflow";
import WorkflowSteps from "../components/WorkflowSteps";

export default function WorkflowChat() {
  const [message, setMessage] = useState("");
  const { accessToken } = useAuth()

  const {
    loading,
    threadId,
    route,
    steps,
    answer,
    result,
    error,
    sendMessage,
    cancel,
  } = useWorkflow(accessToken);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!message.trim()) return;

    await sendMessage(message);
  }

  return (
    <main style={{ maxWidth: 900, margin: "40px auto" }}>
      <h1>ManuAgent 智能制造助手</h1>

      <form onSubmit={handleSubmit}>
        <textarea
          value={message}
          onChange={(event) =>
            setMessage(event.target.value)
          }
          placeholder="例如：分析 CNC-001 最近的故障原因"
          rows={4}
          style={{ width: "100%" }}
        />

        <div style={{ marginTop: 12 }}>
          <button type="submit" disabled={loading}>
            {loading ? "分析中..." : "开始分析"}
          </button>

          {loading && (
            <button
              type="button"
              onClick={cancel}
              style={{ marginLeft: 12 }}
            >
              停止接收
            </button>
          )}
        </div>
      </form>

      {threadId && (
        <p>Thread ID：{threadId}</p>
      )}

      {route && <p>Agent 路由：{route}</p>}

      <WorkflowSteps steps={steps} />

      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}

      {answer && (
        <section>
          <h3>分析结果</h3>
          <p style={{ whiteSpace: "pre-wrap" }}>
            {answer}
          </p>
        </section>
      )}

      {result && (
        <section>
          <h3>执行状态</h3>
          <p>{result.status}</p>

          <p>知识引用：{result.sources.length} 条</p>

          <p>分析图表：{result.charts.length} 个</p>
        </section>
      )}
    </main>
  );
}
