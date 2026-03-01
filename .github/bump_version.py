#!/usr/bin/env python3
"""Bump version in marketplace.json based on changelog.d/ fragments."""

import json
import os
import sys

CHANGELOG_DIR = "changelog.d"
MARKETPLACE_PATH = ".claude-plugin/marketplace.json"

# Lower number = higher priority bump
BUMP_PRIORITY = {
    "breaking": 0,  # major
    "added": 1,     # minor
    "removed": 1,   # minor
    "changed": 2,   # patch
    "fixed": 2,     # patch
}


def get_current_version():
    with open(MARKETPLACE_PATH) as f:
        data = json.load(f)
    return data["version"]


def get_bump_level():
    """Scan fragment filenames to determine the highest-priority bump type."""
    level = None
    for fname in os.listdir(CHANGELOG_DIR):
        if fname == ".gitkeep":
            continue
        # Expected format: {name}.{type}.md
        parts = fname.rsplit(".", 2)
        if len(parts) != 3 or parts[2] != "md":
            continue
        fragment_type = parts[1]
        priority = BUMP_PRIORITY.get(fragment_type, 2)  # default to patch
        if level is None or priority < level:
            level = priority
    return level


def compute_new_version(version, level):
    major, minor, patch = map(int, version.split("."))
    if level == 0:
        return f"{major + 1}.0.0"
    elif level == 1:
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def main():
    fragments = [f for f in os.listdir(CHANGELOG_DIR) if f != ".gitkeep"]
    if not fragments:
        print("No changelog fragments found. Nothing to bump.")
        sys.exit(0)

    old_version = get_current_version()
    level = get_bump_level()
    if level is None:
        print("No valid fragments found. Nothing to bump.")
        sys.exit(0)

    new_version = compute_new_version(old_version, level)

    # String replacement preserves JSON formatting
    with open(MARKETPLACE_PATH) as f:
        content = f.read()

    content = content.replace(
        f'"version": "{old_version}"',
        f'"version": "{new_version}"',
    )

    with open(MARKETPLACE_PATH, "w") as f:
        f.write(content)

    print(f"Bumped version: {old_version} → {new_version}")


if __name__ == "__main__":
    main()
