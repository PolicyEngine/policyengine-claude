---
description: Audit a PolicyEngine Next.js zone app for multi-zone compliance — basePath, assetPrefix, vercel.json, host rewrites, cross-zone links
---

# Multi-zone Audit: $ARGUMENTS

**READ-ONLY MODE**: This command audits an existing PolicyEngine Next.js tool for multi-zone compliance and reports findings. It does NOT make code changes.

Use this to verify that a zone will work correctly behind `policyengine.org`, in its own Vercel preview, and in `next dev`.

> **Migration-era command.** This exists to retrofit existing PolicyEngine Next.js tools (built before the multi-zone architecture was standardized) and to verify tools built outside the `/create-dashboard` flow. Once all PolicyEngine Next.js apps conform to the multi-zone architecture, this command can be removed — new apps created via `/create-dashboard` are already validated by the dashboard validators at scaffold time.

## Scope

This command audits **Next.js zone apps** — tools that deploy as a zone behind `policyengine-app-v2/website/`. It does not apply to:

- `policyengine-app-v2` itself (the host — different rules)
- Legacy iframe-embedded tools (not yet migrated to multi-zone)
- Non-Next.js tools (Python/Modal dashboards, static GitHub Pages sites)

The underlying agent (`multizone-validator`) detects these cases and stops with a clear message.

## Options

- `--repo OWNER/NAME` — Audit a specific GitHub repo (clones it to `/tmp`)
- `--path ABSOLUTE_PATH` — Audit a local path (e.g., a worktree or sibling clone)
- No arguments — Audit the current working directory

## Examples

```bash
/audit-multizone                                        # Audit current working directory
/audit-multizone --repo PolicyEngine/keep-your-pay-act  # Clone and audit a GitHub repo
/audit-multizone --path /Users/me/Work/household-api-docs
```

## Phase 0: Parse arguments

```
Parse $ARGUMENTS:
- REPO_ARG: value after --repo if present
- PATH_ARG: value after --path if present
- If neither: use current working directory
```

## Phase 1: Resolve target path

**If `--repo OWNER/NAME` is provided:**
```bash
TARGET_PATH=/tmp/audit-multizone-REPO_NAME
if [ ! -d "$TARGET_PATH" ]; then
  gh repo clone OWNER/NAME "$TARGET_PATH"
else
  (cd "$TARGET_PATH" && git pull)
fi
```

**If `--path ABSOLUTE_PATH` is provided:**
```bash
TARGET_PATH=ABSOLUTE_PATH
```

**If no argument:**
```bash
TARGET_PATH=$(pwd)
```

Verify the path exists and contains a `package.json`:
```bash
test -f "$TARGET_PATH/package.json" || {
  echo "ERROR: $TARGET_PATH does not contain a package.json"
  exit 1
}
```

## Phase 2: Resolve host config path

The multi-zone validator needs `policyengine-app-v2/website/next.config.ts` to verify host rewrites. Try in order:

1. **If running inside a policyengine-app-v2 checkout:** use `<repo-root>/website/next.config.ts`
2. **If `/tmp/policyengine-app-v2` exists:** use that
3. **Otherwise:** clone it:
   ```bash
   gh repo clone PolicyEngine/policyengine-app-v2 /tmp/policyengine-app-v2
   (cd /tmp/policyengine-app-v2 && git checkout main && git pull)
   ```

Set `HOST_CONFIG_PATH=<path>/website/next.config.ts`. If the clone fails (no network, no auth), leave it unset — the validator will skip host-side checks and note the skip in its report.

## Phase 3: Invoke the multi-zone validator

Spawn the `multizone-validator` agent via the `Agent` tool with the resolved inputs:

```
Agent({
  description: "Multi-zone compliance audit",
  subagent_type: "multizone-validator",
  prompt: "Audit the zone at TARGET_PATH for multi-zone compliance.

  Required inputs:
  - TARGET_PATH: <resolved target path>
  - HOST_CONFIG_PATH: <resolved host config path, or 'unavailable'>

  Follow the checks and output format defined in your agent spec. Report findings only — do not edit any files."
})
```

## Phase 4: Present report

Relay the validator's structured report to the user verbatim. Do not summarize or paraphrase — the report format is intentional (PASS/FAIL rows with file:line citations and recommended fixes).

After the report, if there are FAIL items, offer:

```
Use AskUserQuestion:
Question: "Want me to help address these findings?"
Options:
  - "Yes, start with the critical failures" — picks highest-priority FAILs and drafts edits
  - "No, I'll handle these separately" — exit silently
```

If the user says yes, draft edits but do NOT apply them without confirmation — the multi-zone rules touch both the zone repo and the host, so changes usually need to land as coordinated PRs.

## Skills referenced

- `policyengine-interactive-tools-skill` — Authoritative multi-zone rules
- `policyengine-vercel-deployment-skill` — Vercel-side implications

## Related commands

- `/create-dashboard` — Scaffold a new dashboard with multi-zone config baked in
- `/deploy-dashboard` — Deploy a completed dashboard (includes its own host-rewrite pre-flight)
