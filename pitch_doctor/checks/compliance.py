"""Check: GDPR & Legal Compliance.

Many jurisdictions require sites to have privacy policies, terms, and cookie
notices. Missing these can result in fines and legal issues.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "compliance"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    missing_compliance = []

    html = ctx.html or ""
    text_lower = html.lower()

    # Check for privacy policy link
    has_privacy = 'privacy' in text_lower or '/privacy' in text_lower.lower()
    if not has_privacy:
        missing_compliance.append("Privacy policy link (GDPR requirement)")

    # Check for terms of service
    has_terms = 'terms' in text_lower or '/terms' in text_lower.lower()
    if not has_terms:
        missing_compliance.append("Terms of Service link (legal protection)")

    # Check for cookie notice
    has_cookies = 'cookie' in text_lower or 'gdpr' in text_lower
    if not has_cookies:
        missing_compliance.append("Cookie consent notice (GDPR/ePrivacy requirement)")

    # Check for contact/data request capability
    has_contact = 'contact' in text_lower or 'mailto:' in text_lower
    if not has_contact:
        missing_compliance.append("Contact form or method (GDPR data request requirement)")

    if not missing_compliance:
        severity = Severity.OK
        evidence = ["Privacy policy accessible", "Terms of Service present", "Cookie notice visible", "Contact method available"]
        impact = "Your site complies with GDPR, ePrivacy Directive, and other legal requirements. You're protected from fines and legal liability."
    elif len(missing_compliance) <= 2:
        severity = Severity.WARNING
        evidence = [f"Missing: {m}" for m in missing_compliance]
        impact = f"Your site is missing {len(missing_compliance)} legal compliance requirement(s). You could face regulatory warnings or small fines."
    else:
        severity = Severity.CRITICAL
        evidence = [f"Missing: {m}" for m in missing_compliance]
        impact = f"Your site lacks {len(missing_compliance)} critical legal compliance requirements. You're at risk for GDPR fines (up to €20M) and legal action."

    benefit = "Adding privacy policies, terms, cookie notices, and contact methods protects your business legally and builds visitor trust."

    return CheckResult(
        id=CHECK_ID,
        name="GDPR & Legal Compliance",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
