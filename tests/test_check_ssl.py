from __future__ import annotations

from pitch_doctor.checks import ssl_check
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_valid_https_is_ok(strings_en):
    ctx = make_context(has_valid_ssl=True, final_url="https://good.test")
    result = ssl_check.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_no_https_is_critical(strings_en):
    ctx = make_context(has_valid_ssl=False, final_url="http://insecure.test")
    result = ssl_check.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
    assert "Not Secure" in result.impact


def test_invalid_cert_is_critical_in_spanish(strings_es):
    ctx = make_context(
        has_valid_ssl=False,
        final_url="https://badcert.test",
        ssl_error="certificate has expired",
    )
    result = ssl_check.evaluate(ctx, strings_es)
    assert result.severity == Severity.CRITICAL
    assert "No es seguro" in result.impact or "candado" in result.impact.lower() or "seguro" in result.impact.lower()
