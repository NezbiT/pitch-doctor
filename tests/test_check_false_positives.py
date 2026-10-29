from __future__ import annotations

from pitch_doctor.checks import accessibility, analytics_tracking, security_headers, seo_advanced
from pitch_doctor.models import Severity
from tests.conftest import make_context


def _joined(result) -> str:
    return " | ".join(result.evidence)


def test_empty_alt_decorative_image_is_not_flagged(strings_en):
    html = '<html><body><img src="a.svg" alt=""><img src="b.png" alt="Logo"></body></html>'
    result = accessibility.evaluate(make_context(html=html), strings_en)
    assert "images missing alt" not in _joined(result)


def test_img_without_alt_attribute_is_flagged(strings_en):
    html = '<html><body><img src="a.png"><img src="b.png" alt="x"></body></html>'
    result = accessibility.evaluate(make_context(html=html), strings_en)
    assert "1 images missing alt text" in _joined(result)


def test_cloudflare_web_analytics_beacon_is_detected(strings_en):
    html = '<script src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon="{}"></script>'
    result = analytics_tracking.evaluate(make_context(html=html), strings_en)
    assert "Cloudflare Web Analytics" in _joined(result)


def test_noindex_text_in_script_config_is_not_non_indexable(strings_en):
    html = (
        '<html><head><meta name="robots" content="index, follow">'
        '<script>cfg={robotsDisabledValue:"noindex, nofollow"}</script></head></html>'
    )
    result = seo_advanced.evaluate(make_context(html=html), strings_en)
    assert "non-indexable" not in _joined(result)


def test_robots_meta_noindex_is_flagged(strings_en):
    html = '<html><head><meta name="robots" content="noindex, nofollow"></head></html>'
    result = seo_advanced.evaluate(make_context(html=html), strings_en)
    assert "non-indexable" in _joined(result)


def test_csp_frame_ancestors_satisfies_x_frame_options(strings_en):
    headers = {
        "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
        "x-content-type-options": "nosniff",
        "strict-transport-security": "max-age=31536000",
    }
    result = security_headers.evaluate(make_context(headers=headers), strings_en)
    assert result.severity == Severity.OK


def test_missing_x_frame_options_without_frame_ancestors_is_flagged(strings_en):
    headers = {
        "content-security-policy": "default-src 'self'",
        "x-content-type-options": "nosniff",
        "strict-transport-security": "max-age=31536000",
    }
    result = security_headers.evaluate(make_context(headers=headers), strings_en)
    assert "X-Frame-Options" in _joined(result)
