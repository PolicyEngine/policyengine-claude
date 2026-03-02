export interface GateResult {
  passed: boolean;
  gateName: string;
  gateType: "build" | "test" | "type_check";
  durationMs: number;
  details: {
    command: string;
    stdout: string;
    stderr: string;
    exitCode: number;
  };
}

async function runGateCommand(
  command: string,
  cwd: string,
  gateName: string,
  gateType: GateResult["gateType"],
): Promise<GateResult> {
  const start = Date.now();
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

  return {
    passed: exitCode === 0,
    gateName,
    gateType,
    durationMs: Date.now() - start,
    details: {
      command,
      stdout: stdout.slice(-2000),
      stderr: stderr.slice(-2000),
      exitCode,
    },
  };
}

export async function runQualityGate(
  gateType: string,
  cwd: string,
): Promise<GateResult> {
  switch (gateType) {
    case "build":
      return runGateCommand("bun run build", cwd, "bun_build", "build");
    case "test":
      return runGateCommand("bunx vitest run", cwd, "vitest_run", "test");
    case "type_check":
      return runGateCommand("bunx tsc --noEmit", cwd, "tsc_noEmit", "type_check");
    default:
      throw new Error(`Unknown quality gate type: ${gateType}`);
  }
}

/**
 * Run all gates for a phase sequentially. Short-circuits on first failure.
 */
export async function runAllGates(
  gateTypes: string[],
  cwd: string,
): Promise<{ allPassed: boolean; results: GateResult[] }> {
  const results: GateResult[] = [];

  for (const gateType of gateTypes) {
    const result = await runQualityGate(gateType, cwd);
    results.push(result);
    if (!result.passed) {
      return { allPassed: false, results };
    }
  }

  return { allPassed: true, results };
}
