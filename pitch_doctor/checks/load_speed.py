"""Check #1: mobile load speed.

Thresholds: <3s ok, 3-6s warning, >6s critical.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "load_speed"


def severity_for_seconds(seconds: float) -> Severity:
    if seconds < 3:
        return Severity.OK
    if seconds <= 6:
        return Severity.WARNING
    return Severity.CRITICAL


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    seconds = ctx.load_time_seconds
    if seconds is None:
        severity = Severity.CRITICAL
        seconds_str = "N/A"
    else:
        severity = severity_for_seconds(seconds)
        seconds_str = f"{seconds:.1f}"

    evidence = [strings.check_text(CHECK_ID, f"found_{severity.value}", seconds=seconds_str)]
    impact = strings.check_text(CHECK_ID, f"impact_{severity.value}", seconds=seconds_str)
    benefit = strings.check_text(CHECK_ID, "benefit")

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
