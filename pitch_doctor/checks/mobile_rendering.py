"""Check #3: mobile rendering.

Screenshots at iPhone (390x844) and desktop (1440x900) viewports are captured
by the runner and attached to the report so the owner sees their own site.
This module only judges the viewport meta tag and horizontal overflow.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "mobile_rendering"

MINOR_OVERFLOW_PX = 20
MAJOR_OVERFLOW_PX = 50


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    overflow = ctx.mobile_overflow_px or 0
    missing_viewport = not ctx.viewport_meta_present

    issue_fragments = []
    if missing_viewport:
        issue_fragments.append(strings.check_text(CHECK_ID, "issue_viewport"))
    if overflow > MINOR_OVERFLOW_PX:
        issue_fragments.append(strings.check_text(CHECK_ID, "issue_overflow", px=overflow))

    if missing_viewport or overflow > MAJOR_OVERFLOW_PX:
        severity = Severity.CRITICAL
    elif overflow > MINOR_OVERFLOW_PX:
        severity = Severity.WARNING
    else:
        severity = Severity.OK

    issues_str = "; ".join(issue_fragments)
    if severity == Severity.OK:
        evidence = [strings.check_text(CHECK_ID, "found_ok")]
    else:
        evidence = [strings.check_text(CHECK_ID, f"found_{severity.value}", issues=issues_str)]
    impact = strings.check_text(CHECK_ID, f"impact_{severity.value}")
    benefit = strings.check_text(CHECK_ID, "benefit")

    screenshots = [s for s in (ctx.mobile_screenshot_b64, ctx.desktop_screenshot_b64) if s]

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
        screenshots=screenshots,
    )
