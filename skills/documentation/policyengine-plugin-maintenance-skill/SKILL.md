---
name: policyengine-plugin-maintenance
description: |
  Use this skill when updating the policyengine-claude plugin itself — adding skills, fixing skill
  routing, updating years in code examples, reordering skills, or tuning skill descriptions.
  Triggers: "update plugin", "fix skill", "wrong skill loaded", "update year", "plugin maintenance",
  "skill routing", "skill description", "policyengine-claude plugin".
---

# PolicyEngine-Claude plugin maintenance

> **This skill is for maintaining the policyengine-claude plugin itself, not for using PolicyEngine.**

## Plugin architecture

- **Marketplace source**: `~/.claude/plugins/marketplaces/policyengine-claude/`
- **Installed cache**: `~/.claude/plugins/cache/policyengine-claude/complete/<version>/`
- **Plugin registry**: `~/.claude/plugins/installed_plugins.json`
- **Manifest**: `.claude-plugin/marketplace.json` (defines sub-plugins, skill lists, agents)

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

## Skill ordering in marketplace.json

The `complete` sub-plugin's `skills` array determines system prompt order.

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
- Copy changes to cache AND commit to marketplace source

## Making changes effective

### For immediate testing (current machine only)

1. Edit files in marketplace source: `~/.claude/plugins/marketplaces/policyengine-claude/`
2. Copy to cache: `cp <source> ~/.claude/plugins/cache/policyengine-claude/complete/<version>/`
3. Start a new Claude Code session to pick up changes

**Warning**: Cache may be rebuilt from marketplace repo on session start, overwriting manual cache edits. Always commit changes to the marketplace repo.

### For permanent changes

1. Create branch in marketplace repo
2. Make changes and commit
3. Push and create PR
4. After merge, users get updates on next plugin update (`/update-plugins` or automatic)

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
