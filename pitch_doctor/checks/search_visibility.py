"""Check #7: search visibility basics.

Missing/empty title, meta description, Open Graph tags, favicon, or
LocalBusiness JSON-LD structured data.
"""

from __future__ import annotations

from pitch_doctor.checks.base import (
    has_favicon,
    has_local_business_jsonld,
    has_meta_description,
    has_open_graph,
    has_title,
    soupify,
)
from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "search_visibility"

# Missing title or meta description hurts visibility the most.
CRITICAL_FRAGMENT_KEYS = ("issue_title", "issue_meta_description")


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    soup = soupify(ctx.html)

    missing = []
    if not has_title(soup):
        missing.append("issue_title")
    if not has_meta_description(soup):
        missing.append("issue_meta_description")
    if not has_open_graph(soup):
        missing.append("issue_og")
    if not has_favicon(soup):
        missing.append("issue_favicon")
    if not has_local_business_jsonld(soup):
        missing.append("issue_structured_data")

    if not missing:
        severity = Severity.OK
    elif any(key in CRITICAL_FRAGMENT_KEYS for key in missing):
        severity = Severity.CRITICAL
    else:
        severity = Severity.WARNING

    issues_str = "; ".join(strings.check_text(CHECK_ID, key) for key in missing)
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
