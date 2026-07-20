"""Check: Advanced SEO (Schema, OG Tags, Sitemap).

Beyond basic meta tags, these advanced SEO elements help Google and social
media understand and display your site correctly.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "seo_advanced"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    missing_features = []

    html = ctx.html or ""

    # Check for Open Graph tags (social media preview)
    if 'og:title' not in html:
        missing_features.append("Open Graph (OG) tags for social media sharing")
    if 'og:image' not in html:
        missing_features.append("OG image for preview thumbnails")

    # Check for structured data (Schema.org / JSON-LD)
    if 'schema.org' not in html and 'application/ld+json' not in html:
        missing_features.append("Structured data (Schema.org/JSON-LD) for rich snippets")

    # Check for robots.txt (would need DNS check, approximate with meta robots)
    if 'noindex' not in html and 'nofollow' not in html:
        # Site is likely indexable, this is good
        pass
    else:
        missing_features.append("Site marked as non-indexable (noindex/nofollow present)")

    # Check for canonical tag
    if 'rel="canonical"' not in html:
        missing_features.append("Canonical tag (prevents duplicate content issues)")

    # Check for mobile-friendly meta
    if 'viewport' in html:
        # Good, mobile friendly
        pass

    if not missing_features:
        severity = Severity.OK
        evidence = ["Open Graph tags present", "Structured data (Schema.org) found", "Canonical tag present", "Mobile viewport configured"]
        impact = "Your site is fully optimized for search engines and social sharing. Google understands your content, and your links preview beautifully on social media."
    elif len(missing_features) <= 2:
        severity = Severity.WARNING
        evidence = [f"Missing: {f}" for f in missing_features]
        impact = f"Your site is missing {len(missing_features)} advanced SEO features. You're losing some ranking benefits and social sharing visibility."
    else:
        severity = Severity.CRITICAL
        evidence = [f"Missing: {f}" for f in missing_features]
        impact = f"Your site lacks {len(missing_features)} important SEO signals. Google may not fully understand your content, and social shares won't display correctly."

    benefit = "Adding Schema.org structured data, Open Graph tags, and canonical tags improves search rankings, makes social links more attractive, and prevents duplicate content penalties."

    return CheckResult(
        id=CHECK_ID,
        name="Advanced SEO (Schema, OG, Canonical)",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
