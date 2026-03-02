import { runDashboard, initRepository } from "./orchestrator";
import { getConfig } from "./config";
import { askForDescription, askForDashboardName } from "./human-gates";
import { formatDuration } from "./utils";

async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--help") || args.includes("-h")) {
    console.log("PolicyEngine Dashboard Builder SDK\n");
    console.log("Usage:");
    console.log('  bun run sdk/src/index.ts                    # Interactive mode');
    console.log('  bun run sdk/src/index.ts "description..."   # With description\n');
    console.log("Options:");
    console.log("  --skip-init   Skip repo creation (use current directory)\n");
    console.log("Environment variables (see .env.example):");
    console.log("  SUPABASE_URL          (required) Supabase project URL");
    console.log("  SUPABASE_ANON_KEY     (required) Supabase anon key");
    console.log("  PE_DEFAULT_MODEL      (optional) Default model, default: claude-opus-4-6");
    console.log("  PE_TOTAL_BUDGET_USD   (optional) Max spend, default: $25.00");
    console.log("  PE_VERBOSE            (optional) Enable verbose logging");
    process.exit(0);
  }

  // Validate config early
  let config;
  try {
    config = getConfig();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`Configuration error: ${message}`);
    process.exit(1);
  }

  const skipInit = args.includes("--skip-init");
  const positionalArgs = args.filter((a) => !a.startsWith("-"));

  // Get description: from args or interactively
  let description: string;
  if (positionalArgs.length > 0) {
    description = positionalArgs.join(" ");
  } else {
    description = await askForDescription();
  }

  if (!description.trim()) {
    console.error("Error: Dashboard description cannot be empty.");
    process.exit(1);
  }

  // Get dashboard name interactively
  const dashboardName = await askForDashboardName();
  if (!dashboardName.trim()) {
    console.error("Error: Dashboard name cannot be empty.");
    process.exit(1);
  }

  // Initialize repo or use current directory
  let cwd: string;
  if (skipInit) {
    cwd = process.cwd();
    console.log(`\nUsing existing directory: ${cwd}`);
  } else {
    cwd = await initRepository(dashboardName);
  }

  console.log("\nPolicyEngine Dashboard Builder SDK");
  console.log("=".repeat(40));
  console.log(`Dashboard:   ${dashboardName}`);
  console.log(`Directory:   ${cwd}`);
  console.log(`User:        ${config.createdBy}`);
  console.log(`Budget:      $${config.totalBudgetUsd.toFixed(2)}`);
  console.log(`Description: ${description.slice(0, 80)}${description.length > 80 ? "..." : ""}`);
  console.log("=".repeat(40));

  const start = Date.now();

  try {
    await runDashboard(dashboardName, description, cwd);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`\nWorkflow failed: ${message}`);
    console.error(`Total time: ${formatDuration(Date.now() - start)}`);
    process.exit(1);
  }
}

main();
