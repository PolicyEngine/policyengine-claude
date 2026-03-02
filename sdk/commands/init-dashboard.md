---
description: Initialize a new PolicyEngine dashboard repository — creates GitHub repo, clones locally, and sets up the dashboard-builder plugin
---

# Initialize dashboard repository: $ARGUMENTS

Set up a new, empty GitHub repository for a PolicyEngine dashboard and prepare it for the `/create-dashboard` workflow.

**Input:** `$ARGUMENTS` should be the dashboard name in kebab-case (e.g., `child-poverty-dashboard`).

If `$ARGUMENTS` is empty or not valid kebab-case (lowercase letters, numbers, hyphens only), use `AskUserQuestion` to ask:

```
question: "What should the dashboard be called? Use kebab-case (e.g., child-poverty-dashboard)."
header: "Name"
options: [] (free text only — let the user type via "Other")
```

## Step 1: Permission Check

Verify the user can create repositories in the PolicyEngine GitHub organization:

```bash
gh api orgs/PolicyEngine/memberships/$( gh api user --jq '.login' ) --jq '.role' 2>&1
```

**If the command succeeds** and returns `admin` or `member`: proceed to Step 2.

**If the command fails** (404, 403, or any error): stop immediately and display:

> **Permission check failed.** This workflow needs to create a new repository under the `PolicyEngine` GitHub organization, but your current GitHub account does not appear to have the required permissions.
>
> To use this workflow, you need:
> - **Membership** in the [PolicyEngine GitHub organization](https://github.com/PolicyEngine)
> - **Repository creation** privileges within the org
>
> Please ask a PolicyEngine org admin to add your GitHub account, then try again.

**Do NOT proceed past this point if the permission check fails.**

## Step 2: Create GitHub Repository

```bash
gh repo create PolicyEngine/DASHBOARD_NAME --public --clone=false --description "PolicyEngine DASHBOARD_NAME dashboard"
```

**If the repo already exists:** Stop and tell the user:

> Repository `PolicyEngine/DASHBOARD_NAME` already exists. If you want to work on it, clone it manually:
> ```bash
> gh repo clone PolicyEngine/DASHBOARD_NAME
> ```
> Then open a Claude Code session in that directory and run `/create-dashboard`.

## Step 3: Confirm Clone Location

Determine the default clone location — the parent directory of the current working directory:

```bash
dirname "$(pwd)"
```

Use `AskUserQuestion` to confirm:

```
question: "Where should the repo be cloned?"
header: "Clone path"
options:
  - label: "PARENT_DIR/DASHBOARD_NAME (Recommended)"
    description: "Same parent directory as your current working directory"
  - label: "Choose a different path"
    description: "You'll type the full path you want"
```

If the user selects "Other" or "Choose a different path", use their provided path. Use the confirmed path for the next step.

## Step 4: Clone the Repository

```bash
gh repo clone PolicyEngine/DASHBOARD_NAME CONFIRMED_PATH/DASHBOARD_NAME
```

## Step 5: Set Up Plugin Configuration

Create `.claude/settings.json` in the cloned repository so that the `dashboard-builder` plugin is automatically available when opening a Claude Code session in the repo:

```bash
mkdir -p CONFIRMED_PATH/DASHBOARD_NAME/.claude
```

Write `.claude/settings.json` with this content:

```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["dashboard-builder@policyengine-claude"]
  }
}
```

This gives the repo access to `/create-dashboard`, `/deploy-dashboard`, `/dashboard-overview`, and all dashboard builder agents and skills.

## Step 6: Initial Commit and Push

```bash
cd CONFIRMED_PATH/DASHBOARD_NAME
git add -A
git commit -m "Initialize dashboard repository with dashboard-builder plugin"
git push -u origin main
```

## Step 7: Next Steps

Present the following to the user:

> ## Dashboard repository initialized
>
> - **Repository:** https://github.com/PolicyEngine/DASHBOARD_NAME
> - **Local path:** `CONFIRMED_PATH/DASHBOARD_NAME`
>
> ### Next steps
>
> 1. Open a new Claude Code session in the dashboard directory:
>    ```bash
>    cd CONFIRMED_PATH/DASHBOARD_NAME
>    claude
>    ```
> 2. Describe your dashboard using the `/create-dashboard` command:
>    ```
>    /create-dashboard A dashboard that shows...
>    ```
>
> The `/create-dashboard` command will walk you through planning, building, and validating the dashboard.

## Error Recovery

| Issue | Action |
|-------|--------|
| Permission check fails | Stop, display permission message |
| Repo already exists on GitHub | Stop, suggest cloning the existing repo |
| Clone fails | Check network, verify `gh` auth with `gh auth status` |
| Push fails | Check that the repo was created, verify git remote |
