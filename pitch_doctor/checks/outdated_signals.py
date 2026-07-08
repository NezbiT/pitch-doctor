"""Check #4: outdated signals.

Looks for a copyright year in the footer that lags the current year.
current_year - 1 or older is a warning; current_year - 2 or older is critical.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pitch_doctor.checks.base import footer_text, latest_year_in_text, soupify
from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "outdated_signals"


def evaluate(ctx: ScanContext, strings: Strings, *, current_year: int | None = None) -> CheckResult:
    current_year = current_year or datetime.now(UTC).year
    soup = soupify(ctx.html)
    footer = footer_text(soup)
    year = latest_year_in_text(footer)

    if year is None:
        severity = Severity.OK
    elif year <= current_year - 2:
        severity = Severity.CRITICAL
    elif year == current_year - 1:
        severity = Severity.WARNING
    else:
        severity = Severity.OK

    if severity == Severity.OK and year is None:
        evidence = [strings.check_text(CHECK_ID, "found_ok")]
    else:
        evidence = [strings.check_text(CHECK_ID, f"found_{severity.value}", year=year)]
    impact = strings.check_text(CHECK_ID, f"impact_{severity.value}", year=year)
    benefit = strings.check_text(CHECK_ID, "benefit")

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
