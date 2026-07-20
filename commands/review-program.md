---
description: Review any PR — code validation + PDF audit in one pass (read-only, no code changes)
---

# Reviewing PR: $ARGUMENTS

Compatibility stub. The `review-program` skill shipped in this plugin is the real entry
point — current Claude Code gives a skill precedence over a same-named command, so this
file normally never runs. If it does run (older Claude Code versions), do exactly one
thing: invoke the `review-program` skill via the Skill tool, passing `$ARGUMENTS`
through unchanged, and follow it. The skill loads the canonical workflow
(`skills/review-program/references/workflow.md`) and the Claude adapter
(`skills/review-program/references/claude-launcher.md`); do not define or improvise any
workflow behavior here.
