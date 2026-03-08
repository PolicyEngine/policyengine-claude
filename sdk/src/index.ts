#!/usr/bin/env bun
import { runDashboard, initRepository } from "./orchestrator";
import { getConfig } from "./config";
import { askForDescription, askForDashboardName } from "./human-gates";
import { formatDuration } from "./utils";
import { readFileSync, existsSync, statSync } from "fs";
import { resolve, basename, dirname, join } from "path";
import { homedir } from "os";

/**
 * Resolve a repo argument to an absolute path.
 * Accepts a full path or just a name — searches common locations for the name.
 */
function resolveRepo(arg: string): string {
  // Absolute path — use directly
  if (arg.startsWith("/")) {
    if (!existsSync(arg) || !statSync(arg).isDirectory()) {
      console.error(`Error: ${arg} is not a directory.`);
      process.exit(1);
    }
    return arg;
  }

  // Relative path with slashes — resolve from cwd
  if (arg.includes("/")) {
    const resolved = resolve(process.cwd(), arg);
    if (existsSync(resolved) && statSync(resolved).isDirectory()) {
      return resolved;
    }
    console.error(`Error: ${resolved} is not a directory.`);
    process.exit(1);
  }

  // Just a name — search common locations
  const name = arg;
  const searchPaths = [
    // Sibling of cwd
    join(dirname(process.cwd()), name),
    // Under ~/Documents/PolicyEngine/
    join(homedir(), "Documents", "PolicyEngine", name),
    // Under ~/PolicyEngine/
    join(homedir(), "PolicyEngine", name),
    // Under ~/
    join(homedir(), name),
  ];

  for (const candidate of searchPaths) {
    if (existsSync(candidate) && statSync(candidate).isDirectory()) {
      return candidate;
    }
  }

  console.error(`Error: Could not find repo "${name}". Searched:`);
  for (const p of searchPaths) {
    console.error(`  ${p}`);
  }
  process.exit(1);
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--help") || args.includes("-h")) {
    console.log("PolicyEngine Dashboard Builder SDK\n");
    console.log("Usage:");
    console.log('  pe-dashboard                         # Interactive mode');
    console.log('  pe-dashboard "description..."        # With description');
    console.log('  pe-dashboard --prompt spec.md        # Load description from markdown file');
    console.log('  pe-dashboard --repo my-dashboard     # Use existing repo (auto-finds it)');
    console.log('  pe-dashboard --skip-init "desc..."   # Use current directory\n');
    console.log("Options:");
    console.log("  --prompt FILE    Read dashboard description from a markdown file");
    console.log("  --repo PATH      Use existing repo: full path, or just a name to search for");
    console.log("  --skip-init      Skip repo creation (use current directory)");
    console.log("  --no-telemetry   Run without Supabase telemetry\n");
    console.log("Environment variables (see .env.example):");
    console.log("  SUPABASE_URL             Supabase project URL (required unless --no-telemetry)");
    console.log("  SUPABASE_PUBLISHABLE_KEY Supabase publishable key (required unless --no-telemetry)");
    console.log("  PE_DEFAULT_MODEL         Default model, default: claude-opus-4-6");
    console.log("  PE_TOTAL_BUDGET_USD      Max spend, default: $35.00");
    console.log("  PE_VERBOSE               Enable verbose logging");
    process.exit(0);
  }

  // Set telemetry flag before config loads
  if (args.includes("--no-telemetry")) {
    process.env.PE_NO_TELEMETRY = "true";
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
  const promptIdx = args.indexOf("--prompt");
  const repoIdx = args.indexOf("--repo");
  const flagArgIndices = new Set<number>();
  if (promptIdx !== -1) flagArgIndices.add(promptIdx + 1);
  if (repoIdx !== -1) flagArgIndices.add(repoIdx + 1);
  const positionalArgs = args.filter(
    (a, i) => !a.startsWith("-") && !flagArgIndices.has(i),
  );

  // Get description: from --prompt file, positional args, or interactively
  let description: string;
  if (promptIdx !== -1) {
    const filePath = args[promptIdx + 1];
    if (!filePath) {
      console.error("Error: --prompt requires a file path.");
      process.exit(1);
    }
    try {
      description = readFileSync(filePath, "utf-8");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`Error reading prompt file: ${message}`);
      process.exit(1);
    }
  } else if (positionalArgs.length > 0) {
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

  // Resolve working directory: --repo, --skip-init, or create new
  let cwd: string;
  if (repoIdx !== -1) {
    const repoArg = args[repoIdx + 1];
    if (!repoArg) {
      console.error("Error: --repo requires a path or repo name.");
      process.exit(1);
    }
    cwd = resolveRepo(repoArg);
    console.log(`\nUsing existing repo: ${cwd}`);
  } else if (skipInit) {
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
  console.log(`Telemetry:   ${config.telemetryEnabled ? "enabled" : "disabled"}`);
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
