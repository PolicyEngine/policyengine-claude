import { execSync } from "child_process";

export interface Config {
  supabaseUrl: string;
  supabasePublishableKey: string;
  defaultModel: string;
  totalBudgetUsd: number;
  maxValidationIterations: number;
  verbose: boolean;
  createdBy: string;
}

let cachedConfig: Config | null = null;

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `Missing required environment variable: ${name}. See .env.example`,
    );
  }
  return value;
}

function resolveGitHubUser(): string {
  try {
    return execSync("gh api user --jq '.login'", {
      encoding: "utf-8",
      timeout: 10_000,
    }).trim();
  } catch {
    return process.env.USER ?? "unknown";
  }
}

export function getConfig(): Config {
  if (cachedConfig) return cachedConfig;

  cachedConfig = {
    supabaseUrl: requireEnv("SUPABASE_URL"),
    supabasePublishableKey: requireEnv("SUPABASE_PUBLISHABLE_KEY"),
    defaultModel: process.env.PE_DEFAULT_MODEL ?? "claude-opus-4-6",
    totalBudgetUsd: parseFloat(process.env.PE_TOTAL_BUDGET_USD ?? "25.00"),
    maxValidationIterations: parseInt(
      process.env.PE_MAX_VALIDATION_ITERATIONS ?? "3",
      10,
    ),
    verbose: process.env.PE_VERBOSE === "true",
    createdBy: resolveGitHubUser(),
  };

  return cachedConfig;
}
