---
description: Implement a new government benefit program with research, approved scope, validation, and review
---

# Implementing $ARGUMENTS in PolicyEngine (v2)

Compatibility stub. The `encode-policy-v2` skill shipped in this plugin is the real entry
point—current Claude Code gives a skill precedence over a same-named command, so this file
normally never runs. If it does run on an older Claude Code version, do exactly one thing:
invoke the `encode-policy-v2` skill through the Skill tool, pass `$ARGUMENTS` unchanged,
and follow it. The skill loads the canonical workflow
(`skills/encode-policy-v2/references/workflow.md`) and Claude adapter
(`skills/encode-policy-v2/references/claude-launcher.md`); do not define or improvise
workflow behavior here.
