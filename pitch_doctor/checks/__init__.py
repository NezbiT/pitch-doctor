"""One module per V1 check. Each module exposes a pure ``evaluate(ctx, strings)``
function so decision logic can be unit tested against static HTML fixtures with
no live network access. All network/browser I/O lives in ``runner.py``.
"""

from pitch_doctor.checks import (
    accessibility,
    analytics_tracking,
    broken_links,
    compliance,
    contact_friction,
    load_speed,
    mobile_rendering,
    mobile_ux_advanced,
    outdated_signals,
    performance_optimization,
    reachability,
    search_visibility,
    security_headers,
    seo_advanced,
    ssl_check,
    user_experience,
)

ALL_CHECKS = (
    reachability,
    ssl_check,
    security_headers,
    load_speed,
    mobile_rendering,
    mobile_ux_advanced,
    outdated_signals,
    broken_links,
    contact_friction,
    search_visibility,
    seo_advanced,
    accessibility,
    compliance,
    user_experience,
    analytics_tracking,
    performance_optimization,
)

__all__ = ["ALL_CHECKS"]
