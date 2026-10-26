
export type WorkflowStatus =
  | "pending"
  | "running"
  | "completed"
  | "partial"
  | "failed";

export type StepStatus =
  | "pending"
  | "success"
  | "failed";

export interface WorkflowStep {
  id?: number;
  step_id?: number;
  agent: string;
  task?: string;
  status: StepStatus;
  output?: string;
  duration_ms?: number | null;
  attempts?: number;
  sql?: string | null;
  chart?: Record<string, unknown> | null;
}

export interface WorkflowResult {
  thread_id: string;
  workflow_id: string;
  status: WorkflowStatus;
  route: string;
  route_reason: string;
  answer: string;
  steps: WorkflowStep[];
  sources: unknown[];
  charts: unknown[];
  execution_events: unknown[];
}

export type WorkflowEventName =
  | "workflow_started"
  | "route_completed"
  | "plan_created"
  | "step_completed"
  | "step_failed"
  | "workflow_completed"
  | "workflow_failed";

export interface WorkflowEvent {
  event: WorkflowEventName;
  data: Record<string, unknown>;
}
