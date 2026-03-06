import { getSupabase } from "./client";
import { getConfig } from "../config";
import type { PhaseResult } from "../phases/types";

export async function createDashboardRun(
  dashboardName: string,
  description: string,
  cwd: string,
  createdBy: string,
): Promise<string> {
  if (!getConfig().telemetryEnabled) return "no-telemetry";

  const { data, error } = await getSupabase()
    .from("dashboard_runs")
    .insert({
      dashboard_name: dashboardName,
      description,
      cwd,
      status: "running",
      created_by: createdBy,
    })
    .select("id")
    .single();

  if (error) throw new Error(`Failed to create dashboard run: ${error.message}`);
  return data.id;
}

export async function recordPhaseStart(
  runId: string,
  phaseName: string,
  agentName: string,
  model: string,
  phaseOrder: number,
  promptHash: string,
  iteration: number = 1,
): Promise<string> {
  if (!getConfig().telemetryEnabled) return "no-telemetry";

  const { data, error } = await getSupabase()
    .from("phase_runs")
    .insert({
      run_id: runId,
      phase_name: phaseName,
      agent_name: agentName,
      model,
      phase_order: phaseOrder,
      status: "running",
      prompt_hash: promptHash,
      iteration,
    })
    .select("id")
    .single();

  if (error) throw new Error(`Failed to record phase start: ${error.message}`);
  return data.id;
}

export async function recordPhaseEnd(
  phaseRunId: string,
  result: PhaseResult | null,
  status: "completed" | "failed",
  errorMessage?: string,
): Promise<void> {
  if (!getConfig().telemetryEnabled) return;

  const update: Record<string, unknown> = {
    status,
    completed_at: new Date().toISOString(),
  };

  if (result) {
    update.duration_ms = result.durationMs;
    update.duration_api_ms = result.durationApiMs;
    update.num_turns = result.numTurns;
    update.input_tokens = result.inputTokens;
    update.output_tokens = result.outputTokens;
    update.cost_usd = result.costUsd;
    update.session_id = result.sessionId;
  }

  if (errorMessage) update.error_message = errorMessage;

  const { error } = await getSupabase()
    .from("phase_runs")
    .update(update)
    .eq("id", phaseRunId);

  if (error) throw new Error(`Failed to record phase end: ${error.message}`);
}

export async function recordQualityGate(
  phaseRunId: string,
  runId: string,
  gateType: string,
  gateName: string,
  passed: boolean,
  durationMs: number,
  details: Record<string, unknown> = {},
): Promise<void> {
  if (!getConfig().telemetryEnabled) return;

  const { error } = await getSupabase()
    .from("quality_gates")
    .insert({
      phase_run_id: phaseRunId,
      run_id: runId,
      gate_type: gateType,
      gate_name: gateName,
      passed,
      duration_ms: durationMs,
      details,
    });

  if (error) throw new Error(`Failed to record quality gate: ${error.message}`);
}

export async function completeDashboardRun(
  runId: string,
  totals: {
    totalDurationMs: number;
    totalCostUsd: number;
    totalInputTokens: number;
    totalOutputTokens: number;
    planYaml?: Record<string, unknown>;
    finalValidationReport?: Record<string, unknown>;
    gitBranch?: string;
    gitCommitSha?: string;
  },
): Promise<void> {
  if (!getConfig().telemetryEnabled) return;

  const { error } = await getSupabase()
    .from("dashboard_runs")
    .update({
      status: "completed",
      completed_at: new Date().toISOString(),
      total_duration_ms: totals.totalDurationMs,
      total_cost_usd: totals.totalCostUsd,
      total_input_tokens: totals.totalInputTokens,
      total_output_tokens: totals.totalOutputTokens,
      plan_yaml: totals.planYaml,
      final_validation_report: totals.finalValidationReport,
      git_branch: totals.gitBranch,
      git_commit_sha: totals.gitCommitSha,
    })
    .eq("id", runId);

  if (error) throw new Error(`Failed to complete dashboard run: ${error.message}`);
}

export async function failDashboardRun(
  runId: string,
  totalDurationMs: number,
): Promise<void> {
  if (!getConfig().telemetryEnabled) return;

  const { error } = await getSupabase()
    .from("dashboard_runs")
    .update({
      status: "failed",
      completed_at: new Date().toISOString(),
      total_duration_ms: totalDurationMs,
    })
    .eq("id", runId);

  if (error) {
    console.error(`Failed to mark dashboard run as failed: ${error.message}`);
  }
}
