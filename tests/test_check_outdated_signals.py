from __future__ import annotations

from pitch_doctor.checks import outdated_signals
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_current_year_footer_is_ok(strings_en, good_html):
    ctx = make_context(html=good_html)
    result = outdated_signals.evaluate(ctx, strings_en, current_year=2026)
    assert result.severity == Severity.OK


def test_stale_footer_year_is_critical(strings_en, bad_html):
    ctx = make_context(html=bad_html)
    result = outdated_signals.evaluate(ctx, strings_en, current_year=2026)
    assert result.severity == Severity.CRITICAL
    assert "2018" in result.impact


def test_one_year_old_footer_is_warning(strings_en):
    html = "<html><body><footer>Copyright 2025 Acme</footer></body></html>"
    ctx = make_context(html=html)
    result = outdated_signals.evaluate(ctx, strings_en, current_year=2026)
    assert result.severity == Severity.WARNING


def test_no_year_found_is_ok(strings_en):
    html = "<html><body><footer>Acme Inc.</footer></body></html>"
    ctx = make_context(html=html)
    result = outdated_signals.evaluate(ctx, strings_en, current_year=2026)
    assert result.severity == Severity.OK
