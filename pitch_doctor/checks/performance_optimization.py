"""Check: Performance Optimization Details.

Beyond basic load speed, these technical optimizations reduce bandwidth,
improve Core Web Vitals, and reduce server load.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "performance_optimization"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    headers = ctx.headers or {}
    html = ctx.html or ""

    optimization_issues = []

    # Check for gzip compression
    encoding = headers.get('content-encoding', headers.get('Content-Encoding', ''))
    if 'gzip' not in encoding.lower() and 'br' not in encoding.lower():
        optimization_issues.append("Gzip/Brotli compression not detected (larger file size)")

    # Check for caching headers
    cache_control = headers.get('cache-control', headers.get('Cache-Control', ''))
    if not cache_control or 'no-cache' in cache_control.lower():
        optimization_issues.append("Missing or poor cache headers (browsers re-download every visit)")

    # Check for minified CSS/JS (heuristic: look for unminified indicators)
    if '.css' in html or '.js' in html:
        # Hard to detect perfectly, but look for common signs
        if 'style>' in html and '  ' in html.split('style>')[1] if 'style>' in html else False:
            optimization_issues.append("CSS may not be minified (check for inline styles)")

    # Check for lazy loading
    if 'loading="lazy"' not in html and 'decoding="async"' not in html:
        optimization_issues.append("Images not using lazy loading (all images download immediately)")

    # Check for WebP or modern image formats
    if '.webp' not in html.lower():
        optimization_issues.append("Modern image formats (WebP) not used (larger file sizes)")

    # Check for excessive third-party scripts
    script_count = html.count('<script')
    if script_count > 10:
        optimization_issues.append(f"Many scripts detected ({script_count}) - may slow down page")

    if not optimization_issues:
        severity = Severity.OK
        evidence = ["Gzip compression enabled", "Cache headers configured", "Lazy loading used", "WebP images deployed"]
        impact = "Your site is highly optimized. Pages load fast, bandwidth is minimized, and Core Web Vitals are strong."
    elif len(optimization_issues) <= 2:
        severity = Severity.WARNING
        evidence = optimization_issues
        impact = f"Your site has {len(optimization_issues)} optimization opportunity/ies. Pages are slower and consume more bandwidth than needed."
    else:
        severity = Severity.CRITICAL
        evidence = optimization_issues
        impact = f"Your site has {len(optimization_issues)} performance problems. Pages are slow, bandwidth-heavy, and fail Core Web Vitals."

    benefit = "Implementing gzip, caching, lazy loading, and modern image formats makes pages faster, saves bandwidth, and improves SEO rankings."

    return CheckResult(
        id=CHECK_ID,
        name="Performance Optimization",
        severity=severity,
        evidence=evidence,
        impact=impact,
        recommendation=benefit,
    )
