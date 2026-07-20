"""Check: Analytics & Conversion Tracking.

Analytics tools measure visitor behavior and conversions. Without them, you're
flying blind -- you can't optimize what you can't measure.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "analytics_tracking"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    html = ctx.html or ""

    tracking_tools = []

    # Check for Google Analytics
    if 'google-analytics' in html.lower() or 'gtag' in html.lower() or 'GA_MEASUREMENT_ID' in html:
        tracking_tools.append("Google Analytics (GA4)")

    # Check for Facebook Pixel
    if 'facebook.com/tr' in html.lower() or 'fbq(' in html.lower():
        tracking_tools.append("Facebook Pixel")

    # Check for Google Tag Manager
    if 'gtm.js' in html.lower() or 'GTM-' in html:
        tracking_tools.append("Google Tag Manager")

    # Check for conversion tracking (UTM params or similar)
    if 'utm_' in html.lower():
        tracking_tools.append("UTM campaign tracking")

    # Check for event tracking JS
    if 'gtag(' in html.lower() or '.track(' in html.lower():
        tracking_tools.append("Custom event tracking")

    if len(tracking_tools) >= 2:
        severity = Severity.OK
        evidence = [f"Found: {tool}" for tool in tracking_tools]
        impact = f"Your site has comprehensive tracking ({len(tracking_tools)} tools). You can see how visitors behave and measure ROI."
    elif len(tracking_tools) == 1:
        severity = Severity.WARNING
        evidence = [f"Found: {tool}" for tool in tracking_tools]
        impact = "Your site has basic tracking, but you're missing insights from additional sources (social, conversions, etc)."
    else:
        severity = Severity.CRITICAL
        evidence = ["No tracking tools detected"]
        impact = "Your site has no analytics. You can't measure visitors, traffic sources, or conversions. You're flying blind."

    benefit = "Adding Google Analytics, Facebook Pixel, and conversion tracking lets you see visitor journeys, identify drop-off points, and calculate ROI."

    return CheckResult(
        id=CHECK_ID,
        name="Analytics & Conversion Tracking",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
