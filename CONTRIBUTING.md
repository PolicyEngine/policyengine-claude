# Contributing to PolicyEngine Claude

## Development Workflow

### Testing Changes Locally

Use `--plugin-dir` to load the plugin directly without caching:

```bash
claude --plugin-dir /path/to/policyengine-claude
```

This bypasses the cache and picks up changes on restart.

### Publishing Changes

**Versions and CHANGELOG.md are managed automatically.** Do NOT manually edit version fields in `marketplace.json` or `CHANGELOG.md`.

1. Make your changes
2. Add a changelog fragment:
   ```bash
   echo "Description of your change" > changelog.d/my-change.added.md
   ```
   Fragment filename format: `{name}.{type}.md`

   Types: `added`, `changed`, `fixed`, `removed`, `breaking`
3. Commit and push — CI enforces that every PR includes at least one fragment
4. On merge to main, CI automatically:
   - Bumps the version in `marketplace.json` (`breaking` → major, `added`/`removed` → minor, `changed`/`fixed` → patch)
   - Generates a new `CHANGELOG.md` entry from all fragments
   - Deletes consumed fragments
5. Users can then `/plugin update` to get the new version

### Adding New Skills

1. Create directory: `skills/<category>/<skill-name>-skill/`
2. Add `SKILL.md` with frontmatter:
   ```yaml
   ---
   name: skill-name
   description: Clear description with trigger phrases for when to use this skill
   ---
   ```
3. Add the skill path to the relevant plugin(s) in `marketplace.json`
4. Add a changelog fragment to `changelog.d/` (version is bumped automatically on merge)
5. Test with `--plugin-dir` before pushing
