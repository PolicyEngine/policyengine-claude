"""Add country-model skill-loading context without an extra model call.

Claude hook contract: https://code.claude.com/docs/en/hooks#sessionstart
This reminder does not itself load a skill or certify that a worker did so.
"""

import json
from pathlib import Path
import sys


PACKAGES = ("policyengine_us", "policyengine_uk", "policyengine_canada")
EVENTS = {"SessionStart", "SubagentStart"}
CONTEXT = (
    "This is a PolicyEngine country-model repository. Model implementation, "
    "test-authoring and review roles, including encoding/review coordinators, "
    "require policyengine-model-development loaded with the Skill tool in each "
    "agent's own context before substantive work, followed by its "
    "relevant references. Resolve the available installed skill name and follow "
    "references/agent-loading.md: SKILLS_READY includes successful load evidence; "
    "SKILLS_BLOCKED identifies an unavailable skill/tool before substantive work. "
    "A parent load, dispatch instruction or agent type is not proof of a worker "
    "load. The active workflow owns agent selection and stages; this reminder "
    "does not add validators, fixers or pushers, or itself load any skills."
)


def context_for(event: dict) -> dict | None:
    """Return the hook output for a country-model checkout, otherwise None."""
    name = event.get("hook_event_name")
    cwd = event.get("cwd")
    if name not in EVENTS or not isinstance(cwd, str) or not cwd:
        return None
    root = Path(cwd).resolve()
    if not any(
        (candidate / package).is_dir()
        for candidate in (root, *root.parents)
        for package in PACKAGES
    ):
        return None
    return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": CONTEXT}}


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return  # A malformed or empty event never produces output or an error.
    if not isinstance(event, dict):
        return
    output = context_for(event)
    if output is not None:
        print(json.dumps(output))


if __name__ == "__main__":
    main()
