"""One module per V1 check. Each module exposes a pure ``evaluate(ctx, strings)``
function so decision logic can be unit tested against static HTML fixtures with
no live network access. All network/browser I/O lives in ``runner.py``.
"""

from pitch_doctor.checks import (
    broken_links,
    contact_friction,
    load_speed,
    mobile_rendering,
    outdated_signals,
    reachability,
    search_visibility,
    ssl_check,
)

ALL_CHECKS = (
    reachability,
    ssl_check,
    load_speed,
    mobile_rendering,
    outdated_signals,
    broken_links,
    contact_friction,
    search_visibility,
)

__all__ = ["ALL_CHECKS"]
