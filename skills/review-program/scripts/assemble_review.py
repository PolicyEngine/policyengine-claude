#!/usr/bin/env python3
"""Assemble local review reports from selected Markdown findings, without rewriting them."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from check_source_manifest import check_manifest


SECTIONS = {
    "critical": "Critical",
    "should_address": "Should Address",
    "suggestion": "Suggestions",
}
STATES = {"OPEN", "STILL OPEN", "RESOLVED", "UNVERIFIED", "WITHDRAWN"}


def local_path(value: str, root: Path) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Artifact outside RUN_ROOT: {value}")
    return path


def markdown_section(path: Path, heading: str) -> tuple[str, str]:
    """Select one exact heading, retaining nested headings and fenced code verbatim."""
    lines = path.read_text().splitlines(keepends=True)
    headings = []
    fence = None
    for index, line in enumerate(lines):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line) if fence is None else None
        if match:
            headings.append((index, len(match[1]), match[2]))
    matches = [h for h in headings if h[2] == heading]
    if len(matches) != 1:
        raise ValueError(f"Expected one heading {heading!r} in {path}")
    start, level, title = matches[0]
    stop = next(
        (i for i, depth, _ in headings if i > start and depth <= level), len(lines)
    )
    body = "".join(lines[start + 1 : stop]).strip()
    if not body:
        raise ValueError(f"Empty finding: {heading}")
    return title, body


def assemble(data: dict, root: Path, prefix: str) -> dict:
    if not prefix or ".." in prefix or any(char in prefix for char in "/\\*?[]"):
        raise ValueError(
            "Prefix must be a filename component without '..' or glob characters"
        )
    if data.get("version") != 1:
        raise ValueError("Expected assembly input version 1")
    metadata = data["metadata"]
    labels = {
        "Base repository": "repository",
        "PR number": "pr_number",
        "Reviewed head SHA": "head",
        "Merge base SHA": "merge_base",
        "Mode": "mode",
        "Scope": "scope",
    }
    for key in (*labels.values(), "worktree_root"):
        if not str(metadata.get(key, "")).strip():
            raise ValueError(f"Missing metadata: {key}")
    if data.get("status") not in ("COMPLETE", "PARTIAL"):
        raise ValueError("Status must be COMPLETE or PARTIAL")
    roles = data["roles"]
    if not roles or any(role["status"] not in ("DONE", "PARTIAL") for role in roles):
        raise ValueError(
            "Wait for role completion; recover or mark missing work PARTIAL"
        )
    role_paths = {local_path(role["path"], root) for role in roles}
    for path in role_paths:
        if not path.is_file():
            raise ValueError(f"Missing role report: {path}")
    gaps = list(data["gaps"])
    if any(not isinstance(gap, str) or not gap.strip() for gap in gaps):
        raise ValueError("Gaps must be nonempty descriptions")
    notes = list(data.get("notes", []))
    if any(not isinstance(note, str) or not note.strip() for note in notes):
        raise ValueError("Notes must be nonempty descriptions")
    manifest = local_path(data["source_manifest"], root)
    evidence = check_manifest(manifest, Path(metadata["worktree_root"]), root)
    if evidence["rejected"] or evidence["discarded_derivatives"]:
        raise ValueError(
            "Source integrity check rejected evidence; repair the manifest and re-evaluate dependent findings before assembly"
        )
    seen = set()
    findings = []
    for item in data["findings"]:
        finding_id, severity = item["id"], item["severity"]
        state = item.get("status", "OPEN")
        if not re.fullmatch(r"[CAS][1-9][0-9]*", finding_id) or finding_id in seen:
            raise ValueError(f"Invalid or duplicate finding ID: {finding_id}")
        if severity not in SECTIONS or state not in STATES:
            raise ValueError(f"Invalid severity/status: {finding_id}")
        seen.add(finding_id)
        path = local_path(item["path"], root)
        if path not in role_paths:
            raise ValueError(f"Finding must come from a completed role report: {path}")
        title, body = markdown_section(path, item["heading"])
        # IDs are coordinator-owned: retain them even after severity changes or deduplication.
        title = re.sub(r"^[CAS][0-9]+\s*(?:—|–|-|:)\s*", "", title)
        findings.append(
            {
                "id": finding_id,
                "severity": severity,
                "status": state,
                "title": title,
                "body": body,
            }
        )
    open_findings = [
        f for f in findings if f["status"] not in ("RESOLVED", "WITHDRAWN")
    ]
    for role in roles:
        if role["status"] == "PARTIAL":
            gaps.append(
                f"Role checks incomplete: {role['path']}; see recovered report."
            )
    for finding in findings:
        if finding["status"] == "UNVERIFIED":
            gaps.append(
                f"{finding['id']} remains unverified; its prior severity is retained."
            )
    if data["status"] == "PARTIAL" and not gaps:
        raise ValueError("A PARTIAL review must describe its missing checks in gaps")
    counts = {key: sum(f["severity"] == key for f in open_findings) for key in SECTIONS}
    partial = (
        data["status"] == "PARTIAL"
        or gaps
        or any(role["status"] == "PARTIAL" for role in roles)
        or any(f["status"] == "UNVERIFIED" for f in findings)
    )
    status = "PARTIAL" if partial else "COMPLETE"
    confirmed_criticals = any(
        f["severity"] == "critical" and f["status"] != "UNVERIFIED"
        for f in open_findings
    )
    severity = (
        "REQUEST_CHANGES"
        if confirmed_criticals
        else ("COMMENT" if partial or counts["should_address"] else "APPROVE")
    )
    validation = data["validation"].strip()
    if not validation:
        raise ValueError(
            "Provide actual validation results, including NOT RUN where applicable"
        )
    timing = data.get("timing", {})
    if timing and "elapsed_seconds" not in timing:
        raise ValueError("Measured timing must include elapsed_seconds")
    for name, value in timing.items():
        if type(value) not in (int, float) or not 0 <= value < float("inf"):
            raise ValueError(f"Invalid measured timing: {name}")
    metrics = (
        "; ".join(
            f"{key.replace('_', ' ')}: {value:.2f}s" for key, value in timing.items()
        )
        or "Not measured."
    )
    source_lines = [
        f"- [{Path(s['path']).name}]({s['url']}) — [cached original](<{s['path']}>)."
        for s in evidence["sources"]
    ]
    lines = ["# Program review", ""]
    lines += [f"{label}: {metadata[key]}  " for label, key in labels.items()]
    lines += [
        f"Source manifest: {manifest}  ",
        f"Review status: {status}",
        "",
        "## Source Documents",
        "",
    ]
    lines += source_lines or [
        "No source documents registered; see scope and validation."
    ]
    for key, label in SECTIONS.items():
        lines += ["", f"## {label}", ""]
        group = [f for f in findings if f["severity"] == key]
        if not group:
            lines.append("None.")
        for f in group:
            lines += [
                f"### {f['id']} — {f['title']} ({f['status']})",
                "",
                f["body"],
                "",
            ]
    lines += ["", "## Evidence Gaps", ""] + (
        [f"- {gap}" for gap in gaps] or ["No material gaps reported."]
    )
    if notes:
        lines += ["", "## Notes", ""] + [f"- {note}" for note in notes]
    lines += [
        "",
        "## Validation Summary",
        "",
        validation,
        "",
        "## Timing",
        "",
        metrics,
        "",
        "## Review Severity",
        "",
        f"{severity}. Open findings: {counts['critical']} critical, {counts['should_address']} should address, {counts['suggestion']} suggestions.",
    ]
    full = root / f"{prefix}-review-full-report.md"
    summary = [
        "# Review summary",
        "",
        f"Review status: {status}",
        f"Review severity: {severity}",
        f"Still-open critical count: {counts['critical']}",
        f"PR: {metadata['repository']}#{metadata['pr_number']}; reviewed head: {metadata['head']}.",
        f"Open findings: {counts['critical']} critical, {counts['should_address']} should address, {counts['suggestion']} suggestions.",
    ]
    summary += [f"- {f['id']} ({f['status']}): {f['title']}" for f in open_findings]
    summary += [f"- Evidence gap: {gap}" for gap in gaps]
    summary += [f"- Note: {note}" for note in notes]
    summary += ["", validation, "", metrics, "", f"[Full report](<{full}>)"]
    result = {
        "status": status,
        "severity": severity,
        "counts": counts,
        "gaps": gaps,
        "notes": notes,
        "finding_states": dict(Counter(f["status"] for f in findings)),
        "source_integrity": evidence,
        "timing": timing,
    }
    # Validate and render everything before replacing any canonical output.
    outputs = {
        full: "\n".join(lines) + "\n",
        root / f"{prefix}-review-summary.md": "\n".join(summary) + "\n",
        root / f"{prefix}-review-result.json": json.dumps(result, indent=2) + "\n",
    }
    for path, content in outputs.items():
        path.write_text(content)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    try:
        path = local_path(str(args.input.resolve()), args.run_root)
        result = assemble(json.loads(path.read_text()), args.run_root, args.prefix)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Cannot assemble review: {error}\n")
    print(
        json.dumps(
            {key: result[key] for key in ("status", "severity", "counts")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
