"""Check #2: SSL / HTTPS.

No HTTPS, or an invalid certificate, is critical -- there is no "warning" tier
because a browser security warning is a binary trust-breaker for visitors.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "ssl"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    if ctx.has_valid_ssl:
        severity = Severity.OK
        detail = ""
    else:
        severity = Severity.CRITICAL
        if ctx.final_url.startswith("http://") or not ctx.final_url.startswith("https://"):
            detail = strings.check_text(CHECK_ID, "detail_no_https")
        else:
            detail = strings.check_text(CHECK_ID, "detail_invalid_cert", error=ctx.ssl_error or "")

    evidence = [strings.check_text(CHECK_ID, f"found_{severity.value}", detail=detail)]
    impact = strings.check_text(CHECK_ID, f"impact_{severity.value}", detail=detail)
    benefit = strings.check_text(CHECK_ID, "benefit")

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
