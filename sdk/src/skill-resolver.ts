import { readdir } from "fs/promises";
import { join } from "path";
import { readFile } from "fs/promises";

const SDK_ROOT = join(import.meta.dir, "..");
const SKILLS_DIR = join(SDK_ROOT, "skills");

let skillMap: Map<string, string> | null = null;

async function buildSkillMap(): Promise<Map<string, string>> {
  if (skillMap) return skillMap;

  skillMap = new Map();

  // Walk skills/{category}/{skill-name}/SKILL.md
  const categories = await readdir(SKILLS_DIR, { withFileTypes: true });

  for (const category of categories) {
    if (!category.isDirectory()) continue;
    const categoryPath = join(SKILLS_DIR, category.name);
    const skills = await readdir(categoryPath, { withFileTypes: true });

    for (const skill of skills) {
      if (!skill.isDirectory()) continue;
      const skillMdPath = join(categoryPath, skill.name, "SKILL.md");
      try {
        await readFile(skillMdPath, "utf-8"); // Verify it exists
        skillMap.set(skill.name, skillMdPath);
      } catch {
        // No SKILL.md in this directory, skip
      }
    }
  }

  return skillMap;
}

export async function resolveSkillPath(skillName: string): Promise<string> {
  const map = await buildSkillMap();

  // Try exact match
  if (map.has(skillName)) return map.get(skillName)!;

  // Try with -skill suffix
  const withSuffix = skillName.endsWith("-skill")
    ? skillName
    : `${skillName}-skill`;
  if (map.has(withSuffix)) return map.get(withSuffix)!;

  // Try matching partial name (e.g., "design" → "policyengine-design-skill")
  for (const [name, path] of map) {
    if (name.includes(skillName)) return path;
  }

  const available = Array.from(map.keys()).join(", ");
  throw new Error(`Skill not found: ${skillName}. Available: ${available}`);
}

export async function loadSkillContent(skillName: string): Promise<string> {
  const skillPath = await resolveSkillPath(skillName);
  return readFile(skillPath, "utf-8");
}

export async function listAvailableSkills(): Promise<string[]> {
  const map = await buildSkillMap();
  return Array.from(map.keys());
}
