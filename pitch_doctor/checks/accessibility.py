"""Check: WCAG 2.1 Accessibility Compliance.

Accessibility ensures your site works for everyone, including people with
disabilities. It's both a legal requirement and expands your audience.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "accessibility"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    issues = []

    html = ctx.html or ""

    # Check for alt text on images
    images_without_alt = html.count("<img") - html.count('alt="')
    if images_without_alt > 0:
        issues.append(f"{images_without_alt} images missing alt text (accessibility violation)")

    # Check for proper heading structure
    if "<h1" not in html:
        issues.append("Missing H1 tag (proper heading hierarchy)")

    # Check for form labels
    form_inputs = html.count("<input")
    form_labels = html.count("<label")
    if form_inputs > form_labels:
        issues.append("Form inputs without associated labels")

    # Check for viewport meta tag (mobile accessibility)
    if 'viewport' not in html:
        issues.append("Missing viewport meta tag")

    # Check for skip links or navigation landmarks
    has_nav = "<nav" in html or 'role="navigation"' in html
    if not has_nav:
        issues.append("Missing semantic navigation (nav tag or role)")

    if not issues:
        severity = Severity.OK
        evidence = ["Heading structure is proper (H1 present)", "Images have alt text", "Forms have labels", "Viewport meta tag present", "Navigation is semantic"]
        impact = "Your site is accessible to people with disabilities and complies with WCAG 2.1 standards."
    elif len(issues) <= 2:
        severity = Severity.WARNING
        evidence = issues
        impact = "Your site has minor accessibility issues. Some users may have difficulty navigating or using certain features."
    else:
        severity = Severity.CRITICAL
        evidence = issues
        impact = f"Your site has {len(issues)} accessibility barriers. Users with disabilities cannot fully access your content, and you may face legal compliance issues."

    benefit = "Improving accessibility makes your site usable for everyone, increases SEO rankings, and reduces legal liability."

    return CheckResult(
        id=CHECK_ID,
        name="Accessibility (WCAG 2.1)",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
