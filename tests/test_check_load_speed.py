from __future__ import annotations

from pitch_doctor.checks import load_speed
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_fast_load_is_ok(strings_en):
    ctx = make_context(load_time_seconds=1.5)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_borderline_load_is_warning(strings_en):
    ctx = make_context(load_time_seconds=4.2)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
    assert "4.2" in result.impact


def test_slow_load_is_critical(strings_en):
    ctx = make_context(load_time_seconds=9.0)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
    assert "9.0" in result.impact


def test_unmeasurable_load_is_critical(strings_en):
    ctx = make_context(load_time_seconds=None)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
