"""Check: Mobile UX Advanced Features.

Mobile users have different needs: bigger touch targets, clearer hierarchy,
and mobile-optimized content. These details make or break mobile experience.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "mobile_ux_advanced"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    html = ctx.html or ""

    mobile_issues = []

    # Check for viewport meta tag (already checked elsewhere, but critical for mobile)
    if 'viewport' not in html:
        mobile_issues.append("Missing viewport meta tag (site not mobile-optimized)")

    # Check for mobile-specific features
    if 'viewport-fit' not in html:
        mobile_issues.append("Not optimized for notched/safe area devices")

    # Check for tap-friendly links (tel: and mailto:)
    if 'tel:' not in html and '<a href="tel:' not in html:
        mobile_issues.append("Phone number not tappable (tel: link missing)")

    # Check for responsive images
    if 'srcset' not in html:
        mobile_issues.append("Images not responsive (srcset missing - may be slow on mobile)")

    # Check for mobile-friendly font size (hard to detect, but check for excessive font size)
    if 'font-size: 1' in html.lower() or 'font-size:1' in html.lower():
        # Potentially okay, using relative sizing
        pass

    # Check for hamburger menu or mobile nav (indicates mobile consideration)
    has_mobile_nav = any(x in html.lower() for x in ['hamburger', 'mobile-menu', 'toggle', 'mobile-nav', 'aria-label="menu"'])
    if not has_mobile_nav:
        mobile_issues.append("No mobile navigation menu detected")

    if not mobile_issues:
        severity = Severity.OK
        evidence = ["Viewport meta tag present", "Images are responsive", "Phone links are tappable", "Mobile navigation implemented"]
        impact = "Your site has excellent mobile optimization. Mobile users have a smooth, native-feeling experience."
    elif len(mobile_issues) <= 2:
        severity = Severity.WARNING
        evidence = mobile_issues
        impact = f"Your site has {len(mobile_issues)} mobile UX issue(s). Some mobile users will have a sluggish or confusing experience."
    else:
        severity = Severity.CRITICAL
        evidence = mobile_issues
        impact = f"Your site has {len(mobile_issues)} critical mobile problems. Mobile users will struggle and likely abandon."

    benefit = "Optimizing for mobile with responsive images, tappable links, and clear navigation keeps mobile users engaged and increases conversion."

    return CheckResult(
        id=CHECK_ID,
        name="Mobile UX Advanced",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
