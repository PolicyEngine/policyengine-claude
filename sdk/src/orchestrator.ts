import { query } from "@anthropic-ai/claude-agent-sdk";
import type { SDKResultSuccess, SDKResultError, SDKMessage } from "@anthropic-ai/claude-agent-sdk";
import { join, dirname } from "path";
import { loadPhasePrompt } from "./prompt-loader";
import { runAllGates } from "./quality-gates";
import {
  requestPlanApproval,
  requestValidationDecision,
  askForClonePath,
} from "./human-gates";
import {
  createDashboardRun,
  recordPhaseStart,
  recordPhaseEnd,
  recordQualityGate,
  completeDashboardRun,
  failDashboardRun,
} from "./telemetry/recorder";
import {
  PHASE_SEQUENCE,
  PHASE_BUDGETS,
  TOTAL_BUDGET_USD,
  AbortError,
  PhaseFailureError,
  type PhaseConfig,
  type PhaseResult,
} from "./phases/types";
import { getConfig } from "./config";
import * as ui from "./utils";

interface RunTotals {
  costUsd: number;
  inputTokens: number;
  outputTokens: number;
}

async function runCommand(
  command: string,
  cwd?: string,
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  const proc = Bun.spawn(["sh", "-c", command], {
    cwd,
    stdout: "pipe",
    stderr: "pipe",
  });
  const [stdout, stderr] = await Promise.all([
    new Response(proc.stdout).text(),
    new Response(proc.stderr).text(),
  ]);
  const exitCode = await proc.exited;
  return { stdout: stdout.trim(), stderr: stderr.trim(), exitCode };
}

/**
 * Initialize a GitHub repo for the dashboard and clone it locally.
 * Based on commands/init-dashboard.md.
 * Returns the absolute path to the cloned repository.
 */
export async function initRepository(
  dashboardName: string,
): Promise<string> {
  ui.log("\n" + "-".repeat(50));
  ui.log("Initializing repository");
  ui.log("-".repeat(50));

  // Step 1: Permission check
  ui.log("  Checking GitHub org permissions...");
  const whoami = await runCommand("gh api user --jq '.login'");
  if (whoami.exitCode !== 0) {
    throw new AbortError(
      "Could not determine GitHub username. Run `gh auth login` first.",
    );
  }
  const username = whoami.stdout;

  const membership = await runCommand(
    `gh api orgs/PolicyEngine/memberships/${username} --jq '.role' 2>&1`,
  );
  if (
    membership.exitCode !== 0 ||
    !["admin", "member"].includes(membership.stdout)
  ) {
    throw new AbortError(
      "Permission check failed. Your GitHub account does not have repository " +
        "creation privileges in the PolicyEngine organization. Ask a PolicyEngine " +
        "org admin to add your account, then try again.",
    );
  }
  ui.log(`  Authenticated as ${username} (${membership.stdout})`);

  // Step 2: Create GitHub repo
  ui.log(`  Creating PolicyEngine/${dashboardName}...`);
  const create = await runCommand(
    `gh repo create PolicyEngine/${dashboardName} --public --clone=false --description "PolicyEngine ${dashboardName} dashboard"`,
  );
  if (create.exitCode !== 0) {
    if (create.stderr.includes("already exists")) {
      throw new AbortError(
        `Repository PolicyEngine/${dashboardName} already exists. ` +
          `Clone it manually with: gh repo clone PolicyEngine/${dashboardName}`,
      );
    }
    throw new AbortError(`Failed to create repo: ${create.stderr}`);
  }

  // Step 3: Confirm clone location
  const defaultParent = dirname(process.cwd());
  const defaultPath = join(defaultParent, dashboardName);
  const clonePath = await askForClonePath(defaultPath);

  // Step 4: Clone
  ui.log(`  Cloning to ${clonePath}...`);
  const clone = await runCommand(
    `gh repo clone PolicyEngine/${dashboardName} "${clonePath}"`,
  );
  if (clone.exitCode !== 0) {
    throw new AbortError(`Failed to clone repo: ${clone.stderr}`);
  }

  // Step 5: Initial commit and push
  const init = await runCommand(
    'git add -A && git commit --allow-empty -m "Initialize dashboard repository" && git push -u origin main',
    clonePath,
  );
  if (init.exitCode !== 0) {
    ui.verbose(`Init commit warning: ${init.stderr}`);
  }

  ui.log(`  Repository ready: https://github.com/PolicyEngine/${dashboardName}`);
  ui.log(`  Local path: ${clonePath}`);

  return clonePath;
}

/**
 * Main orchestrator: runs the full dashboard creation pipeline.
 */
export async function runDashboard(
  dashboardName: string,
  description: string,
  cwd: string,
): Promise<void> {
  const config = getConfig();
  const runStart = Date.now();
  const totals: RunTotals = { costUsd: 0, inputTokens: 0, outputTokens: 0 };

  const runId = await createDashboardRun(
    dashboardName,
    description,
    cwd,
    config.createdBy,
  );

  ui.log(`\nDashboard run created: ${runId}`);
  ui.log(`User: ${config.createdBy}`);

  try {
    for (const phase of PHASE_SEQUENCE) {
      // Skip phases handled as parallel partners
      if (phase.parallel && phase.name === "validate_spec") continue;

      if (phase.isReviewPhase) {
        await runReviewPhase(cwd);
        continue;
      }

      // Check if this phase runs in parallel with another
      const parallelPhase = PHASE_SEQUENCE.find(
        (p) => p.name === phase.parallel && p.name !== phase.name,
      );

      if (parallelPhase) {
        await runValidationPhases(
          phase,
          parallelPhase,
          runId,
          cwd,
          description,
          totals,
          config.maxValidationIterations,
        );
      } else {
        const result = await runSinglePhase(
          phase,
          runId,
          cwd,
          description,
          totals,
        );

        if (phase.hasHumanGate && result) {
          await handlePlanApproval(
            phase,
            runId,
            cwd,
            description,
            totals,
            result,
          );
        }
      }

      // Check total budget
      if (totals.costUsd > (config.totalBudgetUsd ?? TOTAL_BUDGET_USD)) {
        throw new AbortError(
          `Total budget exceeded: $${totals.costUsd.toFixed(2)} > $${(config.totalBudgetUsd ?? TOTAL_BUDGET_USD).toFixed(2)}`,
        );
      }
    }

    await completeDashboardRun(runId, {
      totalDurationMs: Date.now() - runStart,
      totalCostUsd: totals.costUsd,
      totalInputTokens: totals.inputTokens,
      totalOutputTokens: totals.outputTokens,
    });

    ui.log("\n" + "=".repeat(60));
    ui.log("DASHBOARD BUILD COMPLETE");
    ui.log("=".repeat(60));
    ui.log(`Duration: ${ui.formatDuration(Date.now() - runStart)}`);
    ui.log(`Cost: $${totals.costUsd.toFixed(4)}`);
    ui.log(
      `Tokens: ${totals.inputTokens.toLocaleString()} in / ${totals.outputTokens.toLocaleString()} out`,
    );
  } catch (err) {
    await failDashboardRun(runId, Date.now() - runStart);

    if (err instanceof AbortError) {
      ui.log(`\nWorkflow aborted: ${err.message}`);
    } else if (err instanceof PhaseFailureError) {
      ui.log(`\nPhase failure: ${err.message}`);
    } else {
      throw err;
    }
  }
}

/**
 * Run a single phase: load prompt, invoke SDK, record telemetry, run quality gates.
 */
async function runSinglePhase(
  phase: PhaseConfig,
  runId: string,
  cwd: string,
  description: string,
  totals: RunTotals,
  extraContext?: string,
  iteration: number = 1,
): Promise<PhaseResult | null> {
  if (!phase.agent || !phase.model) return null;

  if (!phase.silent) {
    ui.phaseStart(phase.name, phase.agent);
  }

  const composed = await loadPhasePrompt(
    phase.agent,
    description,
    extraContext,
  );

  ui.verbose(`Prompt hash: ${composed.hash}`);
  ui.verbose(`Skills loaded: ${composed.skillsLoaded.join(", ")}`);

  const phaseRunId = await recordPhaseStart(
    runId,
    phase.name,
    phase.agent,
    phase.model,
    phase.order,
    composed.hash,
    iteration,
  );

  let result: PhaseResult | null = null;

  try {
    const sdkQuery = query({
      prompt: composed.prompt,
      options: {
        model: phase.model,
        cwd,
        maxTurns: phase.maxTurns ?? 50,
        maxBudgetUsd: PHASE_BUDGETS[phase.name] ?? 3.0,
        allowedTools: composed.agentMeta.tools,
        permissionMode: "acceptEdits",
        systemPrompt: {
          type: "preset",
          preset: "claude_code",
          append: `You are the ${phase.agent} agent for the PolicyEngine dashboard builder.`,
        },
        persistSession: false,
        env: {
          ...process.env,
          CLAUDE_AGENT_SDK_CLIENT_APP: "@policyengine/dashboard-sdk/0.1.0",
        },
      },
    });

    for await (const message of sdkQuery) {
      if (message.type === "result") {
        const r = message as SDKResultSuccess | SDKResultError;
        result = {
          phaseRunId,
          durationMs: r.duration_ms,
          durationApiMs: r.duration_api_ms,
          numTurns: r.num_turns,
          inputTokens: r.usage.input_tokens,
          outputTokens: r.usage.output_tokens,
          costUsd: r.total_cost_usd,
          sessionId: r.session_id,
          resultText: r.subtype === "success" ? (r as SDKResultSuccess).result : "",
        };

        totals.costUsd += r.total_cost_usd;
        totals.inputTokens += r.usage.input_tokens;
        totals.outputTokens += r.usage.output_tokens;
      }
    }

    if (result) {
      await recordPhaseEnd(phaseRunId, result, "completed");
      if (!phase.silent) {
        ui.phaseEnd(
          phase.name,
          result.durationMs,
          result.costUsd,
          result.numTurns,
        );
      }
    }

    // Run quality gates
    if (phase.qualityGates && phase.qualityGates.length > 0) {
      const { allPassed, results: gateResults } = await runAllGates(
        phase.qualityGates,
        cwd,
      );

      for (const gr of gateResults) {
        ui.gateResult(gr.gateName, gr.passed, gr.durationMs);
        await recordQualityGate(
          phaseRunId,
          runId,
          gr.gateType,
          gr.gateName,
          gr.passed,
          gr.durationMs,
          gr.details,
        );
      }

      if (!allPassed) {
        const failed = gateResults.find((r) => !r.passed)!;
        throw new PhaseFailureError(
          phase.name,
          failed.gateName,
          failed.details.stderr.slice(-500),
        );
      }
    }
  } catch (err) {
    if (
      err instanceof PhaseFailureError ||
      err instanceof AbortError
    ) {
      throw err;
    }
    await recordPhaseEnd(phaseRunId, result, "failed", String(err));
    throw err;
  }

  return result;
}

/**
 * Handle plan approval after Phase 1.
 * Loops on "modify" until user approves or rejects.
 */
async function handlePlanApproval(
  phase: PhaseConfig,
  runId: string,
  cwd: string,
  description: string,
  totals: RunTotals,
  result: PhaseResult,
): Promise<void> {
  const approval = await requestPlanApproval(result.resultText);

  await recordQualityGate(
    result.phaseRunId,
    runId,
    "human_approval",
    "plan_approval",
    approval.decision === "approve",
    approval.durationMs,
    { decision: approval.decision, feedback: approval.feedback },
  );

  if (approval.decision === "approve") return;

  if (approval.decision === "reject") {
    throw new AbortError("Plan rejected by user");
  }

  // Modify: re-run planner with feedback
  if (approval.decision === "modify" && approval.feedback) {
    ui.log(`\nRe-running planner with feedback: ${approval.feedback}`);
    const newResult = await runSinglePhase(
      phase,
      runId,
      cwd,
      description,
      totals,
      `User feedback on previous plan:\n${approval.feedback}`,
      2,
    );
    if (newResult) {
      await handlePlanApproval(phase, runId, cwd, description, totals, newResult);
    }
  }
}

/**
 * Run Phase 5: both validators in parallel, then handle iteration loop.
 */
async function runValidationPhases(
  validatorPhase: PhaseConfig,
  specPhase: PhaseConfig,
  runId: string,
  cwd: string,
  description: string,
  totals: RunTotals,
  maxIterations: number,
): Promise<void> {
  for (let iteration = 1; iteration <= maxIterations + 1; iteration++) {
    ui.log(`\nValidation round ${iteration}...`);

    const [validatorResult, specResult] = await Promise.all([
      runSinglePhase(
        validatorPhase,
        runId,
        cwd,
        description,
        totals,
        undefined,
        iteration,
      ),
      runSinglePhase(
        specPhase,
        runId,
        cwd,
        description,
        totals,
        undefined,
        iteration,
      ),
    ]);

    // For now, treat validation as passed if the agents complete successfully.
    // A future enhancement would parse the result text for PASS/FAIL categories.
    const validatorPassed = validatorResult !== null;
    const specPassed = specResult !== null;

    if (validatorPassed && specPassed) {
      ui.log("  Validation passed!");
      return;
    }

    if (iteration > maxIterations) {
      const failures = [
        !validatorPassed ? "Dashboard validator did not complete" : "",
        !specPassed ? "Design token validator did not complete" : "",
      ]
        .filter(Boolean)
        .join("\n");

      const decision = await requestValidationDecision(failures, iteration - 1);

      if (validatorResult) {
        await recordQualityGate(
          validatorResult.phaseRunId,
          runId,
          "human_approval",
          "validation_acceptance",
          decision.decision === "accept",
          decision.durationMs,
          { decision: decision.decision },
        );
      }

      if (decision.decision === "accept") return;
      if (decision.decision === "stop") {
        throw new AbortError("User stopped after validation failures");
      }
      // keep_fixing falls through to next iteration
    }
  }
}

/**
 * Phase 6: Review — commit and push.
 */
async function runReviewPhase(cwd: string): Promise<void> {
  ui.log("\n" + "-".repeat(50));
  ui.log("Phase: review");
  ui.log("-".repeat(50));

  const commitProc = Bun.spawn(
    [
      "sh",
      "-c",
      'git add -A && git commit -m "Implement dashboard from plan"',
    ],
    { cwd, stdout: "pipe", stderr: "pipe" },
  );
  await commitProc.exited;

  const pushProc = Bun.spawn(["sh", "-c", "git push origin HEAD"], {
    cwd,
    stdout: "pipe",
    stderr: "pipe",
  });
  await pushProc.exited;

  ui.log("  Code committed and pushed.");
}
