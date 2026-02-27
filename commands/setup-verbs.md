---
description: Install PolicyEngine-themed spinner verbs into your Claude Code settings
---

# Install PolicyEngine spinner verbs

Install PolicyEngine-themed spinner verbs (the loading messages that appear while Claude is thinking) into the user's `~/.claude/settings.json`.

## Steps

1. Read the user's current `~/.claude/settings.json`
2. Check if `spinnerVerbs` is already configured
3. If already configured, show the user what's there and ask if they want to replace it
4. If not configured (or user confirms replacement), merge the following `spinnerVerbs` block into their settings JSON, preserving all other existing settings:

```json
"spinnerVerbs": {
  "mode": "replace",
  "verbs": [
    "Microsimulating",
    "Means-testing",
    "Phasing out benefits",
    "Calculating MTRs",
    "Clawing back subsidies",
    "Navigating the subsidy cliff",
    "Modeling counterfactuals",
    "Imputing income",
    "Reweighting the CPS",
    "Parsing the CFR",
    "Adjudicating eligibility",
    "Benchmarking silver plans",
    "Risk-adjusting",
    "Sunsetting provisions",
    "Scoring the bill",
    "Applying the benefit reduction rate",
    "Overfitting"
  ]
}
```

5. Write the updated JSON back to `~/.claude/settings.json` with proper formatting (2-space indent)
6. Tell the user the verbs are installed and they'll see them next time Claude is thinking

**IMPORTANT:** Preserve all existing settings (permissions, hooks, enabledPlugins, etc.). Only add or replace the `spinnerVerbs` key.
