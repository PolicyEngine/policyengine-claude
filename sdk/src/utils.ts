import { getConfig } from "./config";
import type {
  SDKMessage,
  SDKAssistantMessage,
  SDKToolUseSummaryMessage,
  SDKToolProgressMessage,
} from "@anthropic-ai/claude-agent-sdk";

const DIM = "\x1b[2m";
const RESET = "\x1b[0m";
const BOLD = "\x1b[1m";
const CYAN = "\x1b[36m";
const YELLOW = "\x1b[33m";
const GREEN = "\x1b[32m";
const RED = "\x1b[31m";

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

/**
 * Log an SDK streaming message to the console.
 * Handles all message types except stream_event (partial/token-level).
 */
export function logSDKMessage(message: SDKMessage): void {
  switch (message.type) {
    case "assistant": {
      const msg = message as SDKAssistantMessage;
      // Extract text blocks from the assistant message
      for (const block of msg.message.content) {
        if (block.type === "text" && block.text) {
          const truncated =
            block.text.length > 200
              ? block.text.slice(0, 200) + "..."
              : block.text;
          console.log(`  ${DIM}${truncated}${RESET}`);
        } else if (block.type === "tool_use") {
          const input = JSON.stringify(block.input ?? {});
          const truncatedInput =
            input.length > 120 ? input.slice(0, 120) + "..." : input;
          console.log(
            `  ${CYAN}tool:${RESET} ${block.name} ${DIM}${truncatedInput}${RESET}`,
          );
        }
      }
      break;
    }

    case "tool_use_summary": {
      const msg = message as SDKToolUseSummaryMessage;
      console.log(`  ${GREEN}done:${RESET} ${msg.summary}`);
      break;
    }

    case "tool_progress": {
      const msg = message as SDKToolProgressMessage;
      const elapsed = msg.elapsed_time_seconds.toFixed(0);
      // Overwrite the current line for heartbeats
      process.stdout.write(
        `\r  ${DIM}${msg.tool_name} running... ${elapsed}s${RESET}    `,
      );
      break;
    }

    case "system": {
      // SDKMessage "system" type covers multiple subtypes — use a generic cast
      const sys = message as { subtype: string; [key: string]: unknown };

      if (sys.subtype === "task_started") {
        const desc = (sys.description as string) ?? (sys.task_id as string);
        console.log(`\n  ${YELLOW}subagent started:${RESET} ${desc}`);
      } else if (sys.subtype === "task_progress") {
        const elapsed = formatDuration(
          ((sys.usage as { duration_ms: number })?.duration_ms) ?? 0,
        );
        const tool = sys.last_tool_name ? ` (${sys.last_tool_name})` : "";
        const taskId = ((sys.task_id as string) ?? "").slice(0, 8);
        process.stdout.write(
          `\r  ${DIM}subagent ${taskId}... ${elapsed}${tool}${RESET}    `,
        );
      } else if (sys.subtype === "task_notification") {
        const status = sys.status as string;
        const icon = status === "completed" ? GREEN : RED;
        const summary = ((sys.summary as string) ?? "").slice(0, 120);
        const usage = sys.usage as { total_tokens?: number } | undefined;
        const tokens = usage?.total_tokens
          ? ` | ${usage.total_tokens.toLocaleString()} tokens`
          : "";
        console.log(`\n  ${icon}subagent ${status}:${RESET} ${summary}${tokens}`);
      } else if (sys.subtype === "status") {
        if (sys.status === "compacting") {
          console.log(`  ${YELLOW}compacting context...${RESET}`);
        }
      } else if (sys.subtype === "init") {
        const model = sys.model as string;
        const tools = sys.tools as string[] | undefined;
        console.log(
          `  ${DIM}session init: model=${model}, tools=${tools?.length ?? 0}${RESET}`,
        );
      }
      break;
    }

    // Skip stream_event, user, user replay, result (handled separately),
    // and other message types we don't need to display
    default:
      break;
  }
}
