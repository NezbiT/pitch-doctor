from __future__ import annotations

from pitch_doctor.checks import mobile_rendering
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_viewport_present_no_overflow_is_ok(strings_en):
    ctx = make_context(viewport_meta_present=True, mobile_overflow_px=0)
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_missing_viewport_is_critical(strings_en):
    ctx = make_context(viewport_meta_present=False, mobile_overflow_px=0)
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL


def test_large_overflow_is_critical(strings_en):
    ctx = make_context(viewport_meta_present=True, mobile_overflow_px=120)
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL


def test_small_overflow_is_warning(strings_en):
    ctx = make_context(viewport_meta_present=True, mobile_overflow_px=35)
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_screenshots_are_attached_when_present(strings_en):
    ctx = make_context(
        viewport_meta_present=True,
        mobile_overflow_px=0,
        mobile_screenshot_b64="ZmFrZQ==",
        desktop_screenshot_b64="ZmFrZTI=",
    )
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert result.screenshots == ["ZmFrZQ==", "ZmFrZTI="]
