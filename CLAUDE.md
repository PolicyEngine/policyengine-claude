# PolicyEngine Claude — Development Guidelines

## Changelog & Versioning (Required for every PR)

Every PR must include a changelog fragment. CI will block merges without one.

**Add a fragment:**
```bash
echo "Description of your change" > changelog.d/my-change.added.md
```

**Fragment filename format:** `{name}.{type}.md`

| Type | Bump | When to use |
|------|------|-------------|
| `added` | minor | New features, agents, skills, commands |
| `changed` | patch | Modifications to existing behavior |
| `fixed` | patch | Bug fixes |
| `removed` | minor | Removed features |
| `breaking` | major | Backward-incompatible changes |

**Do NOT:**
- Manually edit version fields in `.claude-plugin/marketplace.json`
- Manually edit `CHANGELOG.md`
- Both are auto-generated on merge by `.github/workflows/push.yml`

## Plugin Structure

- **marketplace.json** — `.claude-plugin/marketplace.json` defines all plugins, agents, commands, skills
- **All plugin versions must match** the top-level `version` field (CI enforces this)
- **Skills** live in `skills/<category>/<skill-name>-skill/SKILL.md` with YAML frontmatter (`name`, `description`)
- **Agents** live in `agents/<category>/<agent-name>.md`
- **Commands** live in `commands/<command-name>.md`

## Testing Locally

```bash
claude --plugin-dir /path/to/policyengine-claude
```
