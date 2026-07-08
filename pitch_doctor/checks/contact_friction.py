"""Check #6: contact friction.

Flags phone numbers that aren't wrapped in tel: links, missing email/contact
links, and missing address information.
"""

from __future__ import annotations

from pitch_doctor.checks.base import (
    find_plain_text_phone,
    has_address_hint,
    has_email_or_contact_link,
    has_tappable_phone_link,
    soupify,
)
from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "contact_friction"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    soup = soupify(ctx.html)

    plain_phone_present = find_plain_text_phone(soup)
    tappable_phone_present = has_tappable_phone_link(soup)
    has_contact = has_email_or_contact_link(soup)
    has_address = has_address_hint(soup)

    issues = []
    phone_not_tappable = plain_phone_present and not tappable_phone_present
    if phone_not_tappable:
        issues.append(strings.check_text(CHECK_ID, "issue_phone_not_tappable"))
    if not has_contact:
        issues.append(strings.check_text(CHECK_ID, "issue_no_email"))
    if not has_address:
        issues.append(strings.check_text(CHECK_ID, "issue_no_address"))

    if phone_not_tappable or not has_contact:
        severity = Severity.CRITICAL
    elif not has_address:
        severity = Severity.WARNING
    else:
        severity = Severity.OK

    issues_str = "; ".join(issues)
    if severity == Severity.OK:
        evidence = [strings.check_text(CHECK_ID, "found_ok")]
    else:
        evidence = [strings.check_text(CHECK_ID, f"found_{severity.value}", issues=issues_str)]
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
