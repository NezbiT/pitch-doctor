"""Check: Security Headers & Advanced SSL.

Security headers protect against common web attacks. Missing headers are
a medium risk; they don't break the site but leave it vulnerable.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "security_headers"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    headers = ctx.headers or {}

    missing_headers = []
    if not any(h in headers for h in ["x-frame-options", "X-Frame-Options"]):
        missing_headers.append("X-Frame-Options (clickjacking protection)")
    if not any(h in headers for h in ["x-content-type-options", "X-Content-Type-Options"]):
        missing_headers.append("X-Content-Type-Options (MIME sniffing protection)")
    if not any(h in headers for h in ["content-security-policy", "Content-Security-Policy"]):
        missing_headers.append("Content-Security-Policy (XSS protection)")
    if not any(h in headers for h in ["strict-transport-security", "Strict-Transport-Security"]):
        missing_headers.append("Strict-Transport-Security (HSTS)")

    if not missing_headers:
        severity = Severity.OK
        evidence = ["All critical security headers are present: X-Frame-Options, X-Content-Type-Options, CSP, HSTS."]
        impact = "Your site has strong protection against common web attacks like clickjacking, XSS, and MIME sniffing."
    elif len(missing_headers) <= 2:
        severity = Severity.WARNING
        evidence = [f"Missing security header: {h}" for h in missing_headers]
        impact = f"Missing {len(missing_headers)} important security header(s). Your site is vulnerable to certain attacks."
    else:
        severity = Severity.CRITICAL
        evidence = [f"Missing security header: {h}" for h in missing_headers]
        impact = f"Missing {len(missing_headers)} critical security headers. Your site lacks essential attack protection."

    benefit = "Adding these headers prevents attackers from embedding your site in frames, modifying content type, injecting scripts, and forcing insecure connections."

    return CheckResult(
        id=CHECK_ID,
        name="Security Headers & Protection",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
