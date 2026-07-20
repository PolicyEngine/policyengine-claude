---
description: Apply fixes to a PR based on /review-program findings or PR review comments
---

# Fixing PR: $ARGUMENTS

Compatibility stub. The `fix-pr` skill shipped in this plugin is the real entry point —
current Claude Code gives a skill precedence over a same-named command, so this file
normally never runs. If it does run (older Claude Code versions), do exactly one thing:
invoke the `fix-pr` skill via the Skill tool, passing `$ARGUMENTS` through unchanged,
and follow it. The skill loads the canonical workflow
(`skills/fix-pr/references/workflow.md`) and the Claude adapter
(`skills/fix-pr/references/claude-launcher.md`); do not define or improvise any
workflow behavior here.
