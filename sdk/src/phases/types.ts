export interface PhaseConfig {
  name: string;
  agent: string | null;
  model: string | null;
  order: number;
  qualityGates?: string[];
  hasHumanGate?: boolean;
  /** If true, this phase is a validator run in parallel with other validators */
  isValidator?: boolean;
  /** If true, this phase is the review/commit phase (no agent invocation) */
  isReviewPhase?: boolean;
  /** If true, runs silently without user-facing output */
  silent?: boolean;
  /** Max turns for the agent SDK query */
  maxTurns?: number;
  /** Max retries when quality gates fail (re-runs agent with error context) */
  maxGateRetries?: number;
}

export interface PhaseResult {
  phaseRunId: string;
  durationMs: number;
  durationApiMs: number;
  numTurns: number;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  sessionId: string;
  resultText: string;
}

/** Budget caps per phase in USD */
export const PHASE_BUDGETS: Record<string, number> = {
  plan: 2.0,
  scaffold: 3.0,
  backend: 3.0,
  frontend: 5.0,
  integrate: 3.0,
  validate_build: 2.0,
  validate_design: 2.0,
  validate_architecture: 2.0,
  validate_plan: 3.0,
  review: 0.5,
  overview: 1.0,
};

export const TOTAL_BUDGET_USD = 35.0;

/** The full phase sequence for the dashboard builder pipeline. */
export const PHASE_SEQUENCE: PhaseConfig[] = [
  {
    name: "plan",
    agent: "dashboard-planner",
    model: "claude-opus-4-6",
    order: 1,
    hasHumanGate: true,
    maxTurns: 30,
  },
  {
    name: "scaffold",
    agent: "dashboard-scaffold",
    model: "claude-opus-4-6",
    order: 2,
    qualityGates: ["build", "test"],
    maxGateRetries: 2,
    maxTurns: 50,
  },
  {
    name: "backend",
    agent: "backend-builder",
    model: "claude-opus-4-6",
    order: 3,
    maxTurns: 50,
  },
  {
    name: "frontend",
    agent: "frontend-builder",
    model: "claude-opus-4-6",
    order: 4,
    maxTurns: 50,
  },
  {
    name: "integrate",
    agent: "dashboard-integrator",
    model: "claude-opus-4-6",
    order: 5,
    maxTurns: 50,
  },
  {
    name: "validate_build",
    agent: "dashboard-build-validator",
    model: "claude-opus-4-6",
    order: 6,
    isValidator: true,
    maxTurns: 30,
  },
  {
    name: "validate_design",
    agent: "dashboard-design-validator",
    model: "claude-opus-4-6",
    order: 6,
    isValidator: true,
    maxTurns: 30,
  },
  {
    name: "validate_architecture",
    agent: "dashboard-architecture-validator",
    model: "claude-opus-4-6",
    order: 6,
    isValidator: true,
    maxTurns: 30,
  },
  {
    name: "validate_plan",
    agent: "dashboard-plan-validator",
    model: "claude-opus-4-6",
    order: 6,
    isValidator: true,
    maxTurns: 50,
  },
  {
    name: "review",
    agent: null,
    model: null,
    order: 7,
    isReviewPhase: true,
  },
  {
    name: "overview",
    agent: "dashboard-overview-updater",
    model: "claude-opus-4-6",
    order: 8,
    silent: true,
    maxTurns: 20,
  },
];

export class PhaseFailureError extends Error {
  constructor(
    public phase: string,
    public gate: string,
    public details?: string,
  ) {
    super(
      `Phase "${phase}" failed at gate "${gate}"${details ? `: ${details}` : ""}`,
    );
    this.name = "PhaseFailureError";
  }
}

export class BudgetExceededError extends Error {
  constructor(
    public phase: string,
    public spent: number,
    public limit: number,
  ) {
    super(
      `Phase "${phase}" exceeded budget: $${spent.toFixed(2)} > $${limit.toFixed(2)}`,
    );
    this.name = "BudgetExceededError";
  }
}

export class AbortError extends Error {
  constructor(message: string = "Workflow aborted by user") {
    super(message);
    this.name = "AbortError";
  }
}
