"""Check: User Experience & Conversion Optimization.

Good UX means clear CTAs, trust signals, and frictionless paths to conversion.
Poor UX loses visitors before they even consider your offer.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "user_experience"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    html = ctx.html or ""
    text_lower = html.lower()

    ux_issues = []

    # Check for clear CTA buttons
    cta_keywords = ['contact', 'call', 'book', 'schedule', 'order', 'buy', 'signup', 'register', 'get started']
    has_clear_cta = any(keyword in text_lower for keyword in cta_keywords)
    if not has_clear_cta:
        ux_issues.append("No clear call-to-action (CTA) visible")

    # Check for button elements (instead of just links)
    if '<button' not in html.lower():
        ux_issues.append("No button elements found (poor affordance)")

    # Check for trust signals (testimonials, reviews, guarantees)
    trust_keywords = ['testimonial', 'review', 'case study', 'client', 'customer', 'guarantee', '★', '⭐', 'rating']
    has_trust = any(keyword in text_lower for keyword in trust_keywords)
    if not has_trust:
        ux_issues.append("Missing trust signals (testimonials, reviews, guarantees)")

    # Check for pricing transparency
    price_keywords = ['$', '€', '£', 'price', 'cost', 'plan', 'package']
    has_pricing = any(keyword in text_lower for keyword in price_keywords)
    if not has_pricing:
        ux_issues.append("Pricing not transparent or missing")

    # Check for form complexity (too many input fields)
    input_count = html.count('<input')
    if input_count > 8:
        ux_issues.append(f"Form too long ({input_count} fields - high abandonment rate)")

    if not ux_issues:
        severity = Severity.OK
        evidence = ["Clear CTA present", "Button elements used properly", "Trust signals visible", "Pricing transparent", "Form is concise"]
        impact = "Your site has excellent UX with clear paths to conversion. Visitors know what to do and trust you."
    elif len(ux_issues) <= 2:
        severity = Severity.WARNING
        evidence = ux_issues
        impact = f"Your site has {len(ux_issues)} UX issue(s). Visitors may hesitate or abandon before converting."
    else:
        severity = Severity.CRITICAL
        evidence = ux_issues
        impact = f"Your site has {len(ux_issues)} major UX problems. Visitors get confused about what to do and don't trust you enough to convert."

    benefit = "Improving UX with clear CTAs, trust signals, and concise forms directly increases conversions and customer confidence."

    return CheckResult(
        id=CHECK_ID,
        name="User Experience & CTA Clarity",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
