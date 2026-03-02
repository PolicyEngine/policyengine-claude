import * as readline from "readline";

export interface ApprovalResult {
  decision:
    | "approve"
    | "modify"
    | "reject"
    | "accept"
    | "keep_fixing"
    | "stop";
  feedback?: string;
  durationMs: number;
}

function askQuestion(prompt: string): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(prompt, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

export async function requestPlanApproval(
  planSummary: string,
): Promise<ApprovalResult> {
  const start = Date.now();

  console.log("\n" + "=".repeat(60));
  console.log("PLAN REVIEW");
  console.log("=".repeat(60));
  console.log(planSummary);
  console.log("=".repeat(60));
  console.log("\nOptions:");
  console.log("  [A] Approve - Proceed with implementation");
  console.log("  [M] Modify  - Request changes to the plan");
  console.log("  [R] Reject  - Start over");

  const answer = await askQuestion("\nYour choice (A/M/R): ");

  switch (answer.toUpperCase()) {
    case "A":
      return { decision: "approve", durationMs: Date.now() - start };
    case "M": {
      const feedback = await askQuestion("What changes would you like? ");
      return { decision: "modify", feedback, durationMs: Date.now() - start };
    }
    case "R":
      return { decision: "reject", durationMs: Date.now() - start };
    default:
      // Treat free text as modification feedback
      return {
        decision: "modify",
        feedback: answer,
        durationMs: Date.now() - start,
      };
  }
}

export async function requestValidationDecision(
  failures: string,
  iterationCount: number,
): Promise<ApprovalResult> {
  const start = Date.now();

  console.log("\n" + "=".repeat(60));
  console.log(`VALIDATION FAILURES (after ${iterationCount} fix cycles)`);
  console.log("=".repeat(60));
  console.log(failures);
  console.log("=".repeat(60));
  console.log("\nOptions:");
  console.log("  [A] Accept as-is    - Proceed with remaining issues noted");
  console.log("  [K] Keep fixing     - Try another round of fixes");
  console.log("  [S] Stop            - Stop for manual investigation");

  const answer = await askQuestion("\nYour choice (A/K/S): ");

  switch (answer.toUpperCase()) {
    case "A":
      return { decision: "accept", durationMs: Date.now() - start };
    case "K":
      return { decision: "keep_fixing", durationMs: Date.now() - start };
    case "S":
      return { decision: "stop", durationMs: Date.now() - start };
    default:
      return { decision: "keep_fixing", durationMs: Date.now() - start };
  }
}

export async function askForDescription(): Promise<string> {
  console.log("\nDescribe the dashboard you want to build:");
  console.log("(Include: purpose, policy reforms, charts/visualizations, country)\n");
  return askQuestion("> ");
}

export async function askForDashboardName(): Promise<string> {
  return askQuestion("\nDashboard name (e.g., child-poverty-impact): ");
}

export async function askForClonePath(
  defaultPath: string,
): Promise<string> {
  console.log(`\nWhere should the repo be cloned?`);
  console.log(`  [1] ${defaultPath} (Recommended)`);
  console.log(`  [2] Choose a different path`);

  const answer = await askQuestion("\nYour choice (1/2): ");

  if (answer === "2") {
    return askQuestion("Enter the full path: ");
  }

  return defaultPath;
}
