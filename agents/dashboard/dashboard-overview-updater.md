---
name: dashboard-overview-updater
description: Checks if dashboard ecosystem components changed during a create-dashboard run and updates the dashboard-overview command accordingly
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---

## Thinking Mode

**IMPORTANT**: Use careful, step-by-step reasoning before taking any action. Think through:
1. What the current overview command lists
2. What the marketplace.json currently registers
3. Whether there are any differences
4. What specific updates are needed

# Dashboard Overview Updater Agent

Runs at the end of the `/create-dashboard` workflow. Determines whether any dashboard ecosystem components (agents, commands, or skills) were added, removed, or renamed during the run, and updates the `/dashboard-overview` command content to reflect the current state.

## Input

- The dashboard builder ecosystem after a `/create-dashboard` run has completed

## Output

- Either "Overview is up to date" (no changes needed) or an updated `commands/dashboard-overview.md`

## Workflow

### Step 1: Read Current Ecosystem from Marketplace

Read `.claude-plugin/marketplace.json` and extract the `dashboard-builder` plugin entry. Collect:
- All agents listed in the `agents` array
- All commands listed in the `commands` array
- All skills listed in the `skills` array

Also check the `complete` plugin entry for any dashboard-related items that might only appear there.

### Step 2: Read Current Overview

Read `commands/dashboard-overview.md` and extract:
- All agents listed in the Agents table
- All commands listed in the Commands table
- All skills listed in the Skills table

### Step 3: Compare

Diff the marketplace.json entries against what the overview command lists. Identify:
- New agents not listed in the overview
- New commands not listed in the overview
- New skills not listed in the overview
- Items in the overview that no longer exist in the marketplace
- Items whose descriptions may have changed

### Step 4: Update if Needed

**If changes detected:**
1. Read the frontmatter/description of each new agent, command, or skill file to get its description
2. Update the appropriate table(s) in `commands/dashboard-overview.md`:
   - Add new items in the correct position
   - Remove items no longer in the marketplace
   - Update descriptions if they changed
3. Preserve the existing formatting and table structure

**If no changes detected:**
Report "Overview is up to date" and exit without modifying any files.

## DO NOT

- Create the overview from scratch — only update the existing content
- Modify any files other than `commands/dashboard-overview.md`
- Change the overall structure or layout of the overview
- Run the `/dashboard-overview` command itself
- Add items that are not registered in marketplace.json
