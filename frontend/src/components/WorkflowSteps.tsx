
import type { WorkflowStep } from "../types/workflow";

interface Props {
  steps: WorkflowStep[];
}

export default function WorkflowSteps({ steps }: Props) {
  if (steps.length === 0) {
    return <p>暂无执行步骤</p>;
  }

  return (
    <div>
      <h3>Agent 执行步骤</h3>

      <ol>
        {steps.map((step, index) => (
          <li key={step.id ?? step.step_id ?? index}>
            <strong>{step.agent.toUpperCase()}</strong>

            <span style={{ marginLeft: 12 }}>
              {step.status === "pending"
                ? "等待执行"
                : step.status === "success"
                  ? "执行成功"
                  : "执行失败"}
            </span>

            {step.task && <p>{step.task}</p>}

            {step.duration_ms != null && (
              <small>
                耗时：{step.duration_ms} ms
              </small>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
