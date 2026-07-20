# Codex Subagent Plan: review-program

Use this plan when Codex subagent use is available and authorized.

Codex does not have Claude's named agent types. Simulate each Claude reviewer by spawning a `worker` when the task writes report files and an `explorer` for read-only codebase questions. Every agent must finish by writing its assigned `{RUN_ROOT}/{PREFIX}-review-...` file and returning a one-line completion message.

Subagents can use PolicyEngine skills, but the orchestrator should name them explicitly in each subagent prompt. Do not assume a worker will infer the right skills from the parent context.

## Role Mapping

| Claude role | Codex role | Responsibility | Output |
|---|---|---|---|
| context-analyzer | worker | Analyze saved diff and classify PR scope | `{RUN_ROOT}/{PREFIX}-review-context.md` |
| pdf-collector | worker | Find/download/extract official PDFs and render every page | `{RUN_ROOT}/{PREFIX}-review-pdf-manifest.md` |
| file-lister | worker | List full-audit files when `--full` | `{RUN_ROOT}/{PREFIX}-review-full-filelist.md` |
| regulatory-reviewer | worker | Independently verify legal accuracy | `{RUN_ROOT}/{PREFIX}-review-regulatory.md` |
| reference-checker | worker | Validate references and page numbers | `{RUN_ROOT}/{PREFIX}-review-references.md` |
| code-validator | worker | Audit PolicyEngine code patterns | `{RUN_ROOT}/{PREFIX}-review-code.md` |
| edge-case-checker | worker | Audit test coverage | `{RUN_ROOT}/{PREFIX}-review-tests.md` |
| pdf-audit-{topic} | worker | Compare repo values to assigned PDF pages | `{RUN_ROOT}/{PREFIX}-review-pdf-{topic}.md` |
| verifier-* | worker | Verify cross-refs, external PDFs, mismatches, page numbers | verification report files |
| consolidator | worker | Merge all reports into final review | full report and summary |

## Skills to Pass to Workers

Include these lines in subagent prompts as relevant:

- Regulatory reviewer: "Use `$policyengine-variable-patterns`, `$policyengine-parameter-patterns`, and `$policyengine-code-organization`."
- Reference checker: "Use `$policyengine-parameter-patterns` and `$policyengine-period-patterns`."
- Code validator: "Use `$policyengine-parameter-patterns`, `$policyengine-variable-patterns`, `$policyengine-code-organization`, `$policyengine-code-style`, `$policyengine-aggregation`, and `$policyengine-period-patterns`."
- Test coverage checker: "Use `$policyengine-testing-patterns`, `$policyengine-period-patterns`, and `$policyengine-variable-patterns`."
- PDF audit and verifier workers: "Use `$policyengine-parameter-patterns` and `$policyengine-period-patterns`."
- Consolidator: "Use `$policyengine-review-patterns` for severity and review quality."

## Delegation Pattern

1. Do blocking setup locally: derive the worktree-safe `RUN_ROOT`, parse arguments,
   resolve PR number, determine posting mode, fetch refs, and save the full or incremental
   diff.
2. Spawn context-analyzer. In parallel, start PDF collector if a PDF URL is already known and PDF audit is not skipped.
3. Read only context and manifest summaries locally.
4. If `--full`, spawn file-lister and read only its short output.
5. Spawn all applicable validators in one parallel batch:
   - regulatory-reviewer
   - reference-checker
   - code-validator
   - edge-case-checker
   - PDF audit workers split by topic/page range
6. Spawn verification workers for reported mismatches and page-reference checks.
7. Spawn consolidator after all validators and verifiers complete.
8. Locally read only `{RUN_ROOT}/{PREFIX}-review-summary.md`; post or display the full report according to mode.

Pass concrete `RUN_ROOT`, `WORKTREE_ID`, and `PREFIX` values to every worker. The collector
renders every PDF page; audit workers read only assigned ranges. Never allow a worker to
use process-global `/tmp/{PREFIX}-...` paths.

## Read-Only Contract

All review workers are read-only. They may write only `{RUN_ROOT}/{PREFIX}-review-...` report files and downloaded/rendered source artifacts. They must not edit repository source files or change branches.
