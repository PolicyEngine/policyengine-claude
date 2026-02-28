#!/usr/bin/env python3
"""Build CHANGELOG.md from changelog.d/ fragments."""

import json
import os
import sys
from datetime import date

CHANGELOG_DIR = "changelog.d"
CHANGELOG_PATH = "CHANGELOG.md"
MARKETPLACE_PATH = ".claude-plugin/marketplace.json"

TYPE_HEADING = {
    "added": "Added",
    "changed": "Changed",
    "fixed": "Fixed",
    "removed": "Removed",
    "breaking": "Breaking",
}
TYPE_ORDER = ["Added", "Changed", "Fixed", "Removed", "Breaking"]


def get_current_version():
    with open(MARKETPLACE_PATH) as f:
        data = json.load(f)
    return data["version"]


def get_previous_version():
    """Read the most recent version from existing CHANGELOG.md."""
    with open(CHANGELOG_PATH) as f:
        for line in f:
            if line.startswith("## ["):
                return line.split("[")[1].split("]")[0]
    return "0.0.0"


def read_fragments():
    """Read all fragments and group by type heading."""
    groups = {}
    for fname in sorted(os.listdir(CHANGELOG_DIR)):
        if fname == ".gitkeep":
            continue
        parts = fname.rsplit(".", 2)
        if len(parts) != 3 or parts[2] != "md":
            continue
        fragment_type = parts[1]
        heading = TYPE_HEADING.get(fragment_type, fragment_type.capitalize())
        with open(os.path.join(CHANGELOG_DIR, fname)) as f:
            content = f.read().strip()
        if content:
            groups.setdefault(heading, []).append(content)
    return groups


def build_section(version, groups):
    """Build a Keep a Changelog section."""
    lines = [f"## [{version}] - {date.today().isoformat()}", ""]
    for heading in TYPE_ORDER:
        if heading not in groups:
            continue
        lines.append(f"### {heading}")
        lines.append("")
        for entry in groups[heading]:
            for raw_line in entry.splitlines():
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                if not raw_line.startswith("- "):
                    raw_line = f"- {raw_line}"
                lines.append(raw_line)
        lines.append("")
    return "\n".join(lines)


def update_changelog(new_section, version, old_version):
    """Prepend new section to CHANGELOG.md and add comparison link."""
    with open(CHANGELOG_PATH) as f:
        content = f.read()

    # Insert new section before the first existing ## entry
    marker = "\n## ["
    pos = content.find(marker)
    if pos == -1:
        # No existing entries — append after header
        content = content.rstrip() + "\n\n" + new_section + "\n"
    else:
        header = content[: pos + 1]  # include the trailing newline
        rest = content[pos + 1 :]
        content = header + new_section + "\n" + rest

    # Add comparison link at the top of the link reference section
    link = (
        f"[{version}]: https://github.com/PolicyEngine/"
        f"policyengine-claude/compare/{old_version}...{version}"
    )
    lines = content.split("\n")
    new_lines = []
    link_inserted = False
    for line in lines:
        if not link_inserted and line.startswith("[") and "]: https://" in line:
            new_lines.append(link)
            link_inserted = True
        new_lines.append(line)
    if not link_inserted:
        new_lines.append("")
        new_lines.append(link)
    content = "\n".join(new_lines)

    with open(CHANGELOG_PATH, "w") as f:
        f.write(content)


def delete_fragments():
    """Remove consumed fragments, keeping .gitkeep."""
    for fname in os.listdir(CHANGELOG_DIR):
        if fname == ".gitkeep":
            continue
        os.remove(os.path.join(CHANGELOG_DIR, fname))


def main():
    has_fragments = any(f != ".gitkeep" for f in os.listdir(CHANGELOG_DIR))
    if not has_fragments:
        print("No changelog fragments found. Nothing to build.")
        sys.exit(0)

    version = get_current_version()
    old_version = get_previous_version()
    groups = read_fragments()

    new_section = build_section(version, groups)
    update_changelog(new_section, version, old_version)
    delete_fragments()

    print(f"Built changelog for version {version}")


if __name__ == "__main__":
    main()
