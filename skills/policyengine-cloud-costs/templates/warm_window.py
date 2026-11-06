"""Keep a Modal function warm only inside dated windows, and never after WARM_UNTIL.

Copy into the tool's Modal app file and set APP_NAME, FUNCTION_NAME and the windows.
The function's own decorator keeps min_containers=0, so every deploy starts cold. This
Cron re-applies the current window every 10 minutes, because a deploy resets the
autoscaler to the decorator's values. Record each window in the README's running costs.
"""

from datetime import datetime, timezone

import modal

APP_NAME = "TOOL_NAME"
FUNCTION_NAME = "compute"
# (start, end, containers to keep warm), in UTC.
WARM_WINDOWS = [
    (datetime(2026, 11, 26, 11, 0, tzinfo=timezone.utc), datetime(2026, 11, 26, 18, 0, tzinfo=timezone.utc), 2),
]
WARM_UNTIL = max(end for _, end, _ in WARM_WINDOWS)

app = modal.App(APP_NAME)  # use the tool's existing App object


def containers_for(now: datetime) -> int:
    if now >= WARM_UNTIL:
        return 0
    return next((count for start, end, count in WARM_WINDOWS if start <= now < end), 0)


@app.function(schedule=modal.Cron("*/10 * * * *"), cpu=0.25, memory=256, timeout=60)
def apply_warm_window() -> None:
    warm = containers_for(datetime.now(timezone.utc))
    # For a class, use modal.Cls.from_name(APP_NAME, "ClassName")().update_autoscaler(...).
    modal.Function.from_name(APP_NAME, FUNCTION_NAME).update_autoscaler(min_containers=warm)
    print(f"{FUNCTION_NAME}: min_containers={warm}")
