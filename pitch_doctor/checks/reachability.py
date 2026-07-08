"""Check #8: reachability / uptime.

DNS resolution, response status, redirect chain length, and www vs non-www
consistency. An unreachable site is the most damaging possible finding, since
it costs 100% of visitors rather than a fraction of them.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "reachability"

MAX_HEALTHY_REDIRECT_HOPS = 2


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    if not ctx.dns_resolves:
        severity = Severity.CRITICAL
        detail = strings.check_text(CHECK_ID, "detail_dns_failure")
    elif ctx.error or ctx.status_code is None or ctx.status_code >= 400:
        severity = Severity.CRITICAL
        detail = strings.check_text(
            CHECK_ID, "detail_unreachable", error=ctx.error or f"HTTP {ctx.status_code}"
        )
    elif len(ctx.redirect_chain) > MAX_HEALTHY_REDIRECT_HOPS:
        severity = Severity.WARNING
        detail = strings.check_text(
            CHECK_ID, "detail_redirect_chain", hops=len(ctx.redirect_chain)
        )
    elif ctx.www_mismatch:
        severity = Severity.WARNING
        detail = strings.check_text(CHECK_ID, "detail_www_mismatch")
    else:
        severity = Severity.OK
        detail = ""

    if severity == Severity.OK:
        evidence = [strings.check_text(CHECK_ID, "found_ok", status=ctx.status_code)]
    else:
        evidence = [strings.check_text(CHECK_ID, f"found_{severity.value}", detail=detail)]
    impact = strings.check_text(CHECK_ID, f"impact_{severity.value}")
    benefit = strings.check_text(CHECK_ID, "benefit")

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
