
import { useCallback, useRef, useState } from "react";

import { streamWorkflow } from "../api/workflow";

import type {
  WorkflowResult,
  WorkflowStep,
} from "../types/workflow";

export function useWorkflow(accessToken: string) {
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState("");
  const [route, setRoute] = useState("");
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [answer, setAnswer] = useState("");
  const [result, setResult] =
    useState<WorkflowResult | null>(null);

  const [error, setError] = useState("");

  const controllerRef =
    useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim() || controllerRef.current) {
        return;
      }

      const controller = new AbortController();
      controllerRef.current = controller;

      setLoading(true);
      setThreadId("");
      setRoute("");
      setSteps([]);
      setAnswer("");
      setResult(null);
      setError("");

      try {
        await streamWorkflow(message, accessToken, {
          signal: controller.signal,

          onEvent({ event, data }) {
            switch (event) {
              case "workflow_started":
                setThreadId(String(data.thread_id ?? ""));
                break;

              case "route_completed":
                setRoute(String(data.route ?? ""));
                break;

              case "plan_created":
                setSteps(
                  (
                    (data.steps ?? []) as Array<{
                      id: number;
                      agent: string;
                      task: string;
                    }>
                  ).map((step) => ({
                    ...step,
                    status: "pending",
                  })),
                );
                break;

              case "step_completed":
              case "step_failed":
                setSteps((previous) => {
                  const stepId = Number(data.step_id);

                  const exists = previous.some(
                    (step) =>
                      (step.id ?? step.step_id) === stepId,
                  );

                  if (!exists) {
                    return [
                      ...previous,
                      {
                        step_id: stepId,
                        agent: String(data.agent ?? ""),
                        status:
                          data.status === "success"
                            ? "success"
                            : "failed",
                        duration_ms:
                          typeof data.duration_ms === "number"
                            ? data.duration_ms
                            : null,
                      },
                    ];
                  }

                  return previous.map((step) =>
                    (step.id ?? step.step_id) === stepId
                      ? {
                          ...step,
                          status:
                            data.status === "success"
                              ? "success"
                              : "failed",
                          duration_ms:
                            typeof data.duration_ms === "number"
                              ? data.duration_ms
                              : null,
                        }
                      : step,
                  );
                });
                break;

              case "workflow_completed":
              case "workflow_failed":
                if ("workflow_id" in data) {
                  const response =
                    data as unknown as WorkflowResult;

                  setResult(response);
                  setAnswer(response.answer);
                  setSteps(response.steps);
                } else {
                  setError(
                    String(
                      data.message ?? "工作流执行失败",
                    ),
                  );
                }
                break;
            }
          },
        });
      } catch (err) {
        if (
          err instanceof Error &&
          err.name !== "AbortError"
        ) {
          setError(err.message);
        }
      } finally {
        if (controllerRef.current === controller) {
          controllerRef.current = null;
        }

        setLoading(false);
      }
    },
    [],
  );

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
  }, [accessToken]);

  return {
    loading,
    threadId,
    route,
    steps,
    answer,
    result,
    error,
    sendMessage,
    cancel,
  };
}
