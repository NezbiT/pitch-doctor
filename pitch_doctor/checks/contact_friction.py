"""Check #6: contact friction.

Flags phone numbers that aren't wrapped in tel: links, missing email/contact
links, and missing address information.
"""

from __future__ import annotations

import re

from pitch_doctor.checks.base import (
    has_address_hint,
    has_email_or_contact_link,
    has_tappable_phone_link,
    soupify,
)
from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "contact_friction"

# Pattern to find phone numbers in plain text (used only to determine if a
# *non-tappable* phone number exists on the page).
_PHONE_RE = re.compile(
    r"(?:^|\s)(\+?\d{1,3}[\s.-]?)?\(? \d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}(?:\s|$)",
)


def _plain_phone_in_body(soup) -> bool:
    """Return True if the body text contains at least one raw phone number."""
    body_text = soup.get_text(" ", strip=True) if soup else ""
    return bool(_PHONE_RE.search(body_text))


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    soup = soupify(ctx.html)

    # --- Phone number tappable check ---
    # Only flag as "phone not tappable" if we *actually* find a phone number
    # in the body text that is NOT wrapped in a <a href="tel:...">.
    # A number that appears *only* as a tel: link is fine and should NOT
    # trigger the "phone not tappable" issue.
    has_plain_phone = _plain_phone_in_body(soup)
    has_tappable_phone = has_tappable_phone_link(soup) if soup else False
    phone_not_tappable = has_plain_phone and not has_tappable_phone

    has_contact = has_email_or_contact_link(soup)
    has_address = has_address_hint(soup)

    issues = []
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
