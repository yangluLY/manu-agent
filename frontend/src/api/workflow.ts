
import type {
  WorkflowEvent,
  WorkflowEventName,
} from "../types/workflow";

interface StreamOptions {
  signal?: AbortSignal;
  onEvent: (event: WorkflowEvent) => void;
}

function parseSSE(block: string): WorkflowEvent | null {
  let name = "";
  const dataLines: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      name = line.slice(6).trim();
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (!name || dataLines.length === 0) {
    return null;
  }

  return {
    event: name as WorkflowEventName,
    data: JSON.parse(dataLines.join("\n")),
  };
}

export async function streamWorkflow(
  message: string,
  accessToken: string,
  options: StreamOptions,
): Promise<void> {
  const response = await fetch(
    "/api/v1/workflow/chat/stream",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ message }),
      signal: options.signal,
    },
  );

  if (!response.ok) {
    throw new Error(`请求失败：${response.status}`);
  }

  if (!response.body) {
    throw new Error("浏览器不支持流式读取");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";
  let hasTerminalEvent = false;

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, {
        stream: true,
      });

      buffer = buffer.replace(/\r\n/g, "\n");

      let index: number;

      while ((index = buffer.indexOf("\n\n")) !== -1) {
        const block = buffer.slice(0, index);
        buffer = buffer.slice(index + 2);

        const event = parseSSE(block);

        if (event) {
          options.onEvent(event);

          if (
            event.event === "workflow_completed" ||
            event.event === "workflow_failed"
          ) {
            hasTerminalEvent = true;
          }
        }
      }
    }

    if (!hasTerminalEvent) {
      throw new Error(
        "连接已结束，但没有收到工作流最终事件",
      );
    }
  } finally {
    reader.releaseLock();
  }
}
