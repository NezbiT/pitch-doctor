"""Check #5: broken internal links.

The runner performs up to 25 concurrent HEAD requests against internal links
and hands this module the results as ``ctx.broken_links``: a list of
``(url, status)`` tuples where ``status`` is an int HTTP status >=400, or a
string like "error" for a connection failure.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "broken_links"

WARNING_THRESHOLD = 2  # 1-2 broken links: warning; 3+: critical


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    broken = ctx.broken_links
    checked = len(ctx.internal_links)
    count = len(broken)

    if count == 0:
        severity = Severity.OK
    elif count <= WARNING_THRESHOLD:
        severity = Severity.WARNING
    else:
        severity = Severity.CRITICAL

    examples = ", ".join(f"{url} ({status})" for url, status in broken[:3])

    if severity == Severity.OK:
        evidence = [strings.check_text(CHECK_ID, "found_ok", checked=checked)]
    else:
        evidence = [
            strings.check_text(
                CHECK_ID,
                f"found_{severity.value}",
                checked=checked,
                count=count,
                examples=examples,
            )
        ]
    impact = strings.check_text(CHECK_ID, f"impact_{severity.value}", count=count)
    benefit = strings.check_text(CHECK_ID, "benefit")

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
