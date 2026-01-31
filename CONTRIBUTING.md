# Contributing to PolicyEngine Claude

## Development Workflow

### Testing Changes Locally

Use `--plugin-dir` to load the plugin directly without caching:

```bash
claude --plugin-dir /path/to/policyengine-claude
```

This bypasses the cache and picks up changes on restart.

### Publishing Changes

**IMPORTANT: Always bump the version AND update CHANGELOG.md when making changes.**

Claude Code caches plugins by version. If you push changes without bumping the version, users won't get the updates even after running `/plugin update`.

1. Make your changes
2. Bump the version in `.claude-plugin/marketplace.json`:
   - Bump ALL version fields (marketplace version + each plugin's version)
   - Use semver: patch for fixes, minor for new features, major for breaking changes
3. **Update CHANGELOG.md** (common pitfall - don't forget this!):
   - Add a new section at the top with the new version and today's date
   - Document changes under `### Added`, `### Changed`, `### Fixed`, or `### Removed`
   - `changelog_entry.yaml` is NOT automatically processed - you must update CHANGELOG.md directly
4. Commit and push to main
5. Users can then `/plugin update` to get the new version

Example version bump:
```bash
# Bump from 3.4.0 to 3.4.1
sed -i '' 's/"version": "3.4.0"/"version": "3.4.1"/g' .claude-plugin/marketplace.json
```

Example CHANGELOG.md entry:
```markdown
## [3.4.1] - 2026-01-31

### Changed
- **agent-name** - Description of what changed
```

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
4. Bump the version
5. Test with `--plugin-dir` before pushing
