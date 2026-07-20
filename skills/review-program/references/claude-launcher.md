# Claude Code launcher: review-program

Read this file only when executing the review-program workflow in Claude Code. The
canonical workflow is [workflow.md](workflow.md) — read it first; this file maps its
abstract operations onto Claude Code mechanics and adds nothing else.

## Mechanics

- **"Ask the user"** → `AskUserQuestion` (posting mode, missing PR argument, and any
  canonical checkpoint).
- **Run identity** → after deriving `WORKTREE_ID` and `PREFIX`, create the team:
  `TeamCreate({WORKTREE_ID}-{PREFIX}-review)` and pass
  `team_name: "{WORKTREE_ID}-{PREFIX}-review"` to every agent.
- **"Delegate role X"** → spawn an agent with the type from the table below,
  `run_in_background: true` (except the consolidator, which runs in the foreground),
  and a prompt containing: the role's task spec from the canonical workflow, the
  concrete `RUN_ROOT`/`WORKTREE_ID`/`PREFIX` values, the file paths it reads and
  writes, and the canonical completion-contract DONE line. Include `Load skills:` lines
  naming the role's skills from the canonical Roles table.
- **Namespacing** → plugin agents and skills are namespaced by the *installed plugin*
  (e.g. `complete:country-models:rules-engineer` under the complete bundle, but a
  different prefix under other bundles). Resolve every agent and skill name in this
  file against the session's available lists by suffix match — never assume a specific
  plugin prefix. If a specialized agent is not installed, fall back to
  `general-purpose` and put the role's full task spec and skills in the prompt.
- **"Concurrently"** → spawn all agents of the batch in a single message. The harness
  notifies you as each background agent completes; wait for the whole batch, never
  poll. Apply the canonical stalled-delegate fallback.
- **Coordinator context protection** → you are the coordinator in the canonical
  orchestration contract: read ONLY the short summary files it lists; never read the
  diff, code files, PDF artifacts, or individual finding files.

## Role → agent type

Agent names below are unprefixed; resolve them per the namespacing rule above.

| Canonical role | Agent |
|---|---|
| context-analyzer | `general-purpose` (needs Write) |
| pdf-collector | `document-collector` |
| file-lister | `general-purpose` (needs Write) |
| regulatory-reviewer | `program-reviewer` |
| reference-checker | `reference-validator` |
| code-validator | `implementation-validator` (Mode B — read-only code-pattern audit; do NOT run its structural-fix phases) |
| edge-case-checker | `edge-case-generator` |
| pdf-audit-{topic}, verifier-* | `general-purpose` (need Bash for pdftoppm + Read for PNGs) |
| verification-planner | `general-purpose` (needs Write) |
| consolidator | `general-purpose` (foreground) |
