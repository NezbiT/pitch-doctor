"""Check: User Experience & Conversion Optimization.

Good UX means clear CTAs, trust signals, and frictionless paths to conversion.
Poor UX loses visitors before they even consider your offer.
"""

from __future__ import annotations

import re

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "user_experience"

# Keywords that indicate a visible CTA in the page text (skipped inside
# <script>, <style>, <meta>, <link> because those are not visible to a
# human visitor).  We search the *entire* HTML string but exclude blocks
# that are clearly hidden from the reader.
_CTA_KEYWORDS = [
    "contact", "call", "book", "schedule", "order", "buy",
    "signup", "register", "get started", "call now", "request",
    "quote", "estimate", "free",
]

# Visible text is everything outside <script>, <style>, <meta>, <link>.
_HIDDEN_BLOCK_RE = re.compile(
    r"<(?:script|style|meta|link)[^>]*>.*?</(?:script|style|meta|link)>",
    re.DOTALL | re.IGNORECASE,
)


def _visible_text(html: str) -> str:
    """Return HTML text excluding blocks not visible to a human visitor."""
    cleaned = _HIDDEN_BLOCK_RE.sub("", html)
    # Strip remaining HTML tags
    visible = re.sub(r"<[^>]+>", " ", cleaned)
    return visible.lower()


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    html = ctx.html or ""
    visible = _visible_text(html)

    ux_issues = []

    # --- 1. CTA detection ---
    has_clear_cta = any(kw in visible for kw in _CTA_KEYWORDS)
    if not has_clear_cta:
        ux_issues.append("No clear call-to-action (CTA) visible")

    # --- 2. Button elements ---
    # Tolerate anchor tags that *function* as buttons (contain CTA text).
    has_button_tag = "<button" in html.lower()
    if not has_button_tag:
        cta_link_pat = re.compile(
            r"<a[^>]*>\s*(" + "|".join(re.escape(kw) for kw in _CTA_KEYWORDS) + r")\s*</a>",
            re.IGNORECASE,
        )
        if not cta_link_pat.search(html):
            ux_issues.append("No button elements found (poor affordance)")

    # --- 3. Trust signals ---
    trust_keywords = [
        "testimonial", "review", "case study", "client", "customer",
        "guarantee", "\u2605", "\u2b50", "rating",
    ]
    has_trust = any(kw in visible for kw in trust_keywords)
    if not has_trust:
        ux_issues.append("Missing trust signals (testimonials, reviews, guarantees)")

    # --- 4. Pricing transparency ---
    price_keywords = [
        "$", "\u20ac", "\u00a3", "price", "cost", "plan", "package",
        "starting", "from $",
    ]
    has_pricing = any(kw in visible for kw in price_keywords)
    if not has_pricing:
        ux_issues.append("Pricing not transparent or missing")

    # --- 5. Form complexity ---
    input_count = html.count("<input")
    if input_count > 8:
        ux_issues.append(f"Form too long ({input_count} fields - high abandonment rate)")

    if not ux_issues:
        severity = Severity.OK
        evidence = [
            "Clear CTA present",
            "Button elements used properly",
            "Trust signals visible",
            "Pricing transparent",
            "Form is concise",
        ]
        impact = (
            "Your site has excellent UX with clear paths to conversion. "
            "Visitors know what to do and trust you."
        )
    elif len(ux_issues) <= 2:
        severity = Severity.WARNING
        evidence = ux_issues
        impact = (
            f"Your site has {len(ux_issues)} UX issue(s). "
            "Visitors may hesitate or abandon before converting."
        )
    else:
        severity = Severity.CRITICAL
        evidence = ux_issues
        impact = (
            f"Your site has {len(ux_issues)} major UX problems. "
            "Visitors get confused about what to do and don't trust you enough to convert."
        )

    benefit = (
        "Improving UX with clear CTAs, trust signals, and concise forms "
        "directly increases conversions and customer confidence."
    )

    return CheckResult(
        id=CHECK_ID,
        name="User Experience & CTA Clarity",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
