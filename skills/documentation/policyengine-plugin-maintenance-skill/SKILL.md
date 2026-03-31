---
name: policyengine-plugin-maintenance
description: |
  Use this skill when updating the PolicyEngine skills source repo or the generated
  policyengine-claude wrapper — adding skills, fixing skill routing, updating years in code
  examples, reordering skills, or tuning skill descriptions.
  Triggers: "update plugin", "fix skill", "wrong skill loaded", "update year", "plugin maintenance",
  "skill routing", "skill description", "policyengine-claude plugin", "policyengine-skills".
---

# PolicyEngine skills and Claude wrapper maintenance

> **This skill is for maintaining the PolicyEngine skills source repo and Claude wrapper, not for using PolicyEngine.**

## Plugin architecture

- **Canonical source**: `PolicyEngine/policyengine-skills`
- **Generated wrapper repo**: `PolicyEngine/policyengine-claude`
- **Marketplace source checkout**: `~/.claude/plugins/marketplaces/policyengine-claude/`
- **Installed cache**: `~/.claude/plugins/cache/policyengine-claude/complete/<version>/`
- **Plugin registry**: `~/.claude/plugins/installed_plugins.json`
- **Claude manifest**: `targets/claude/marketplace.template.json` + `bundles/*.json` in source, rendered to `.claude-plugin/marketplace.json` in the generated wrapper

## How skill matching works

1. Each skill has a `SKILL.md` with YAML frontmatter containing `name` and `description`
2. Skill descriptions are listed in the system prompt at session start
3. **Order matters**: skills listed earlier in `marketplace.json` appear first in the system prompt and may get matched preferentially
4. Claude decides whether to invoke a skill via the `Skill` tool based on matching the user query against descriptions
5. If Claude thinks it can handle the task without the skill, it may skip invocation entirely

## Skill description best practices

### Making a skill load reliably

Use "ALWAYS LOAD THIS SKILL FIRST" language (proven pattern from microsimulation skill):

```yaml
description: |
  ALWAYS LOAD THIS SKILL FIRST before writing any PolicyEngine-US code.
  Contains the correct situation dictionary structure, entity names, variable names...
```

### Preventing a skill from loading for wrong queries

Use "ONLY use" + "DO NOT use" pattern:

```yaml
description: |
  ONLY use this skill when users explicitly ask about [specific topic].
  DO NOT use for [common mismatched query type] — use [correct skill] instead.
```

### Trigger phrases

List explicit trigger phrases in the description. Copy the microsimulation skill's pattern:

```yaml
description: |
  Triggers: "keyword1", "keyword2", "phrase one", "phrase two".
```

## Skill ordering in bundle manifests

The `bundles/complete.json` file determines Claude system prompt order for the generated `complete` wrapper.

**Current priority order** (most commonly needed first):
1. `policyengine-us-skill` / `policyengine-uk-skill` (household calculations)
2. `policyengine-user-guide-skill` (web app usage)
3. `policyengine-microsimulation-skill` (population analysis)
4. Other tools-and-apis skills
5. `policyengine-python-client-skill` (last among tools — only for explicit API questions)

**Rule**: Skills that match common user queries should be listed before niche/technical skills.

## Annual year update checklist

Every January (or when the year changes), update ALL code examples:

### Files to update

1. **US skill**: `skills/domain-knowledge/policyengine-us-skill/SKILL.md`
   - All `{YEAR:` keys in situation dictionaries
   - All `.calculate("var", YEAR)` calls
   - All `"period": YEAR` in axes
   - All `"YEAR-01-01.2100-12-31"` in reform definitions
   - The "IMPORTANT" callout year reference

2. **UK skill**: `skills/domain-knowledge/policyengine-uk-skill/SKILL.md`
   - Same pattern as US
   - Also update "Key Parameters and Values (YEAR/YY)" heading

3. **Python client skill**: `skills/tools-and-apis/policyengine-python-client-skill/SKILL.md`
   - All `"YEAR"` string keys
   - All `"YEAR-01-01.2100-12-31"` reform dates

4. **Microsimulation skill**: `skills/tools-and-apis/policyengine-microsimulation-skill/SKILL.md`
   - All `period=YEAR` in calc() calls

### Quick update commands

```bash
# Find all year references across skills
grep -rn "2026" skills/ | grep -v ".git"

# Bulk replace (use with care — review diff before committing)
# Replace year in situation keys
find skills/ -name "SKILL.md" -exec sed -i '' 's/{2026:/{2027:/g' {} +
# Replace year in calculate calls
find skills/ -name "SKILL.md" -exec sed -i '' 's/, 2026)/, 2027)/g' {} +
# Replace year in string keys
find skills/ -name "SKILL.md" -exec sed -i '' 's/"2026"/"2027"/g' {} +
```

### Don't forget

- Update the "IMPORTANT" callout in each skill: `not 2025 or 2026` → `not 2026 or 2027`
- Update reform date ranges: `"2026-01-01.2100-12-31"` → `"2027-01-01.2100-12-31"`
- The UK "Key Parameters and Values" heading with tax year
- Rebuild the Claude wrapper after changing source files

## Making changes effective

### CRITICAL: Cache invalidation

Claude Code caches plugins and **does NOT pick up file edits automatically**. Manually editing
files in the cache directory (`~/.claude/plugins/cache/`) has no effect — Claude Code rebuilds
the cache from the marketplace repo's git state on session start.

**To test local changes:**

```bash
# 1. Make changes in the source repo and commit
cd /path/to/policyengine-skills
# ... edit files, git add, git commit ...

# 2. Rebuild the generated Claude wrapper locally
python3 scripts/build_claude_wrapper.py --source-root . --output-root build/policyengine-claude

# 3. Clear the plugin cache (this is the key step)
rm -rf ~/.claude/plugins/cache/policyengine-claude

# 4. Start a new Claude Code session — it rebuilds from the synced marketplace repo
```

**To publish changes for all users:**

1. Create branch in `policyengine-skills`, make changes, commit, push
2. Create and merge PR to main
3. Let CI sync the generated output to `PolicyEngine/policyengine-claude`
4. Clear cache: `rm -rf ~/.claude/plugins/cache/policyengine-claude`
5. Start new session to verify

## Common issues

### Wrong skill loads for household questions

**Symptoms**: `policyengine-python-client` loads instead of `policyengine-us`
**Fix**:
- Strengthen US/UK descriptions with "ALWAYS LOAD THIS SKILL FIRST"
- Restrict python-client with "ONLY use when explicitly asked about API"
- Ensure US/UK are listed BEFORE python-client in marketplace.json skill order

### Code examples use wrong year

**Symptoms**: Generated code uses 2024/2025 instead of current year
**Fix**: Run the annual year update checklist above

### Skill loads but model ignores its content

**Symptoms**: Skill loads (shown in output) but generated code doesn't match patterns
**Fix**: Add "IMPORTANT" callout boxes with specific instructions at the top of the skill body, not just in the description
