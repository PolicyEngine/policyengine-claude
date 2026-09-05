#!/usr/bin/env python3
"""Validate reusable local evidence without downloading or modifying any files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def checked_file(record: dict, roots: tuple[Path, ...]) -> None:
    if not isinstance(record, dict):
        raise ValueError("file record must be an object")
    raw_path, checksum = record.get("path"), record.get("sha256")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        raise ValueError("file path must be absolute")
    path = Path(raw_path).resolve()
    if not any(path.is_relative_to(root) for root in roots):
        raise ValueError("file is outside this worktree's evidence directories")
    if not isinstance(checksum, str) or len(checksum) != 64:
        raise ValueError("missing or invalid SHA-256")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != checksum:
        raise ValueError("SHA-256 mismatch")


def check_manifest(manifest: Path, worktree_root: Path, run_root: Path) -> dict:
    roots = (run_root.resolve(), (worktree_root / "sources").resolve())
    if not any(manifest.resolve().is_relative_to(root) for root in roots):
        raise ValueError("manifest is outside this worktree's evidence directories")
    data = json.loads(manifest.read_text())
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("expected source manifest version 1")
    recorded_root = data.get("worktree_root")
    if (
        not isinstance(recorded_root, str)
        or not Path(recorded_root).is_absolute()
        or Path(recorded_root).resolve() != worktree_root.resolve()
    ):
        raise ValueError("source manifest belongs to a different worktree")
    if not isinstance(data.get("sources"), list):
        raise ValueError("sources must be a list")
    result = {"sources": [], "rejected": [], "discarded_derivatives": []}
    for source in data["sources"]:
        try:
            checked_file(source, roots)
            if not isinstance(source.get("url"), str) or not source["url"]:
                raise ValueError("original is missing its URL")
        except (OSError, ValueError) as error:
            result["rejected"].append({"source": source, "reason": str(error)})
            continue
        valid = {
            key: value
            for key, value in source.items()
            if key not in ("text", "renders")
        }
        derivatives = []
        if "text" in source:
            derivatives.append(("text", source["text"]))
        renders = source.get("renders", [])
        if isinstance(renders, list):
            derivatives.extend(("render", render) for render in renders)
        else:
            result["discarded_derivatives"].append(
                {"source": source["url"], "reason": "renders must be a list"}
            )
        for kind, derivative in derivatives:
            try:
                checked_file(derivative, roots)
                if derivative.get("source_sha256") != source["sha256"]:
                    raise ValueError("derivative belongs to different original bytes")
                if kind == "render" and any(
                    type(derivative.get(key)) is not int or derivative[key] <= 0
                    for key in ("page", "dpi")
                ):
                    raise ValueError("render needs positive integer page and dpi")
            except (OSError, ValueError) as error:
                result["discarded_derivatives"].append(
                    {
                        "source": source["url"],
                        "derivative": derivative,
                        "reason": str(error),
                    }
                )
                continue
            if kind == "text":
                valid["text"] = derivative
            else:
                valid.setdefault("renders", []).append(derivative)
        result["sources"].append(valid)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--worktree-root", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = check_manifest(args.manifest, args.worktree_root, args.run_root)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cannot reuse source manifest: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
