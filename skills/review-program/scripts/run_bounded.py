#!/usr/bin/env python3
"""Run a review subprocess with a deadline and preserve its stdout for capture."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.seconds <= 0 or not args.command:
        parser.error("a positive deadline and command are required")
    started = time.monotonic()
    label = os.path.basename(args.command[0])
    try:
        process = subprocess.Popen(args.command, start_new_session=True)
    except OSError as error:
        print(f"Cannot start {label}: {error}", file=sys.stderr)
        print(f"{label}: exit status 127", file=sys.stderr)
        return 127
    try:
        status = process.wait(timeout=args.seconds)
    except subprocess.TimeoutExpired:
        # Git/curl may have child processes; terminate the complete process group.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        print(f"{label}: timed out after {args.seconds:g}s", file=sys.stderr)
        status = 124
    finally:
        print(f"{label}: elapsed {time.monotonic() - started:.2f}s", file=sys.stderr)
    exit_status = status if status >= 0 else 128 - status
    print(f"{label}: exit status {exit_status}", file=sys.stderr)
    return exit_status


if __name__ == "__main__":
    raise SystemExit(main())
