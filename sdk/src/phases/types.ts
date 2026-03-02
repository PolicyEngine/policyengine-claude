export interface PhaseConfig {
  name: string;
  agent: string | null;
  model: string | null;
  order: number;
  qualityGates?: string[];
  hasHumanGate?: boolean;
  /** Name of another phase to run in parallel with */
  parallel?: string;
  /** If true, this phase is the review/commit phase (no agent invocation) */
  isReviewPhase?: boolean;
  /** If true, runs silently without user-facing output */
  silent?: boolean;
  /** Max turns for the agent SDK query */
  maxTurns?: number;
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
  validate: 2.0,
  validate_spec: 1.5,
  review: 0.5,
  overview: 0.5,
};

export const TOTAL_BUDGET_USD = 25.0;

/** The full phase sequence matching create-dashboard.md */
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
    maxTurns: 50,
  },
  {
    name: "backend",
    agent: "backend-builder",
    model: "claude-opus-4-6",
    order: 3,
    qualityGates: ["type_check", "test"],
    maxTurns: 50,
  },
  {
    name: "frontend",
    agent: "frontend-builder",
    model: "claude-opus-4-6",
    order: 4,
    qualityGates: ["build", "test"],
    maxTurns: 50,
  },
  {
    name: "integrate",
    agent: "dashboard-integrator",
    model: "claude-sonnet-4-5-20250929",
    order: 5,
    qualityGates: ["build", "test"],
    maxTurns: 50,
  },
  {
    name: "validate",
    agent: "dashboard-validator",
    model: "claude-opus-4-6",
    order: 6,
    parallel: "validate_spec",
    maxTurns: 50,
  },
  {
    name: "validate_spec",
    agent: "dashboard-design-token-validator",
    model: "claude-opus-4-6",
    order: 6,
    parallel: "validate",
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
    model: "claude-sonnet-4-5-20250929",
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
