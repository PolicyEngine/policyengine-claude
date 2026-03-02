import { getConfig } from "./config";

export function log(message: string): void {
  console.log(message);
}

export function verbose(message: string): void {
  if (getConfig().verbose) {
    console.log(`  [verbose] ${message}`);
  }
}

export function phaseStart(phaseName: string, agentName: string): void {
  const line = "-".repeat(50);
  console.log(`\n${line}`);
  console.log(`Phase: ${phaseName} (${agentName})`);
  console.log(`Started: ${new Date().toISOString()}`);
  console.log(line);
}

export function phaseEnd(
  phaseName: string,
  durationMs: number,
  costUsd: number,
  turns: number,
): void {
  const seconds = (durationMs / 1000).toFixed(1);
  console.log(
    `  Completed: ${phaseName} in ${seconds}s | $${costUsd.toFixed(4)} | ${turns} turns`,
  );
}

export function gateResult(
  gateName: string,
  passed: boolean,
  durationMs: number,
): void {
  const status = passed ? "PASS" : "FAIL";
  const seconds = (durationMs / 1000).toFixed(1);
  console.log(`  Gate [${gateName}]: ${status} (${seconds}s)`);
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  const mins = Math.floor(ms / 60_000);
  const secs = ((ms % 60_000) / 1000).toFixed(0);
  return `${mins}m ${secs}s`;
}
