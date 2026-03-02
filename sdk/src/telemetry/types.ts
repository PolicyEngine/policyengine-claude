export interface DashboardRunRow {
  id?: string;
  dashboard_name: string;
  description: string;
  status: "running" | "completed" | "failed" | "aborted";
  started_at?: string;
  completed_at?: string | null;
  total_duration_ms?: number | null;
  total_cost_usd?: number | null;
  total_input_tokens?: number | null;
  total_output_tokens?: number | null;
  plan_yaml?: Record<string, unknown> | null;
  final_validation_report?: Record<string, unknown> | null;
  git_branch?: string | null;
  git_commit_sha?: string | null;
  cwd: string;
  created_by: string;
  metadata?: Record<string, unknown>;
}

export interface PhaseRunRow {
  id?: string;
  run_id: string;
  phase_name: string;
  phase_order: number;
  agent_name: string;
  model: string;
  status: "running" | "completed" | "failed" | "skipped";
  started_at?: string;
  completed_at?: string | null;
  duration_ms?: number | null;
  duration_api_ms?: number | null;
  num_turns?: number | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  cost_usd?: number | null;
  session_id?: string | null;
  iteration: number;
  prompt_hash?: string | null;
  error_message?: string | null;
  metadata?: Record<string, unknown>;
}

export interface QualityGateRow {
  id?: string;
  phase_run_id: string;
  run_id: string;
  gate_type: string;
  gate_name: string;
  passed: boolean;
  checked_at?: string;
  duration_ms?: number | null;
  details?: Record<string, unknown>;
}
