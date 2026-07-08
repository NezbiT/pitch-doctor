from __future__ import annotations

from pitch_doctor.checks import search_visibility
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_complete_meta_is_ok(strings_en, good_html):
    ctx = make_context(html=good_html)
    result = search_visibility.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_missing_everything_is_critical(strings_en, bad_html):
    ctx = make_context(html=bad_html)
    result = search_visibility.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL


def test_missing_only_favicon_and_og_is_warning(strings_en):
    html = """
    <html><head>
      <title>Some Business</title>
      <meta name="description" content="A great local business.">
    </head><body></body></html>
    """
    ctx = make_context(html=html)
    result = search_visibility.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
