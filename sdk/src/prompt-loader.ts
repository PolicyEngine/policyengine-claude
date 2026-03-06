import { readFile } from "fs/promises";
import { join } from "path";
import { createHash } from "crypto";
import { loadSkillContent } from "./skill-resolver";

const REPO_ROOT = join(import.meta.dir, "../..");
const AGENTS_DIR = join(REPO_ROOT, "agents", "dashboard");

export interface AgentMeta {
  name: string;
  model: string;
  tools: string[];
  description: string;
}

export interface ComposedPrompt {
  prompt: string;
  hash: string;
  agentMeta: AgentMeta;
  skillsLoaded: string[];
}

/**
 * Parse YAML frontmatter from an agent .md file.
 * Handles the simple key: value format used in agent definitions.
 */
function parseFrontmatter(content: string): AgentMeta {
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch) {
    return { name: "unknown", model: "opus", tools: [], description: "" };
  }

  const fm = fmMatch[1];
  const get = (key: string): string => {
    const match = fm.match(new RegExp(`^${key}:\\s*(.+)$`, "m"));
    return match ? match[1].trim() : "";
  };

  return {
    name: get("name"),
    model: get("model"),
    tools: get("tools")
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean),
    description: get("description"),
  };
}

/**
 * Extract skill references from the "## Skills Used" section.
 * Looks for patterns like **policyengine-*-skill**
 */
function extractSkillReferences(content: string): string[] {
  const found = new Set<string>();

  // Match **policyengine-...-skill** pattern
  for (const match of content.matchAll(
    /\*\*(policyengine-[\w-]+-skill)\*\*/g,
  )) {
    found.add(match[1]);
  }

  // Match `Skill: policyengine-...-skill` pattern
  for (const match of content.matchAll(
    /Skill:\s*(policyengine-[\w-]+-skill)/g,
  )) {
    found.add(match[1]);
  }

  return Array.from(found);
}

/**
 * Strip the "## First: Load Required Skills" section from the agent body.
 * This section tells the agent to call the Skill tool, which doesn't exist
 * in the SDK — skills are injected into the prompt programmatically.
 */
function stripSkillLoadingInstructions(content: string): string {
  // Remove frontmatter
  const withoutFm = content.replace(/^---\n[\s\S]*?\n---\n*/, "");

  // Remove the skill loading section (everything from that heading to the next ## heading)
  return withoutFm.replace(
    /## First: Load Required Skills[\s\S]*?(?=\n## )/,
    "",
  );
}

/**
 * Map frontmatter tool names to SDK-compatible tool names.
 * Drops tools that don't exist in the Agent SDK (Skill, WebSearch, WebFetch).
 */
function mapToolsToSdk(tools: string[]): string[] {
  const SDK_TOOLS = new Set([
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "Task",
    "WebFetch",
    "WebSearch",
  ]);

  return tools.filter(
    (t) => SDK_TOOLS.has(t) && t !== "Skill",
  );
}

/**
 * Compose a full prompt for an agent by:
 * 1. Reading the agent .md file
 * 2. Parsing frontmatter for metadata
 * 3. Extracting and loading referenced skills
 * 4. Stripping skill-loading instructions
 * 5. Assembling: description + agent body + skill content
 */
export async function loadPhasePrompt(
  agentName: string,
  dashboardDescription: string,
  extraContext?: string,
): Promise<ComposedPrompt> {
  const agentPath = join(AGENTS_DIR, `${agentName}.md`);
  const agentContent = await readFile(agentPath, "utf-8");

  const agentMeta = parseFrontmatter(agentContent);
  agentMeta.tools = mapToolsToSdk(agentMeta.tools);

  const skillNames = extractSkillReferences(agentContent);
  const strippedAgent = stripSkillLoadingInstructions(agentContent);

  // Load all referenced skills
  const skillSections: string[] = [];
  for (const skillName of skillNames) {
    try {
      const content = await loadSkillContent(skillName);
      skillSections.push(
        `\n\n---\n## Loaded Skill: ${skillName}\n\n${content}`,
      );
    } catch (err) {
      console.warn(`Warning: Could not load skill ${skillName}: ${err}`);
    }
  }

  // Compose final prompt
  const parts = [
    `# Dashboard Description\n\n${dashboardDescription}`,
    extraContext ? `\n\n# Additional Context\n\n${extraContext}` : "",
    `\n\n# Agent Instructions\n\n${strippedAgent}`,
    ...skillSections,
  ];

  const prompt = parts.join("");
  const hash = createHash("sha256").update(prompt).digest("hex").slice(0, 16);

  return { prompt, hash, agentMeta, skillsLoaded: skillNames };
}
