from __future__ import annotations

from pitch_doctor.checks import reachability
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_healthy_site_is_ok(strings_en):
    ctx = make_context(dns_resolves=True, status_code=200, redirect_chain=[])
    result = reachability.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_dns_failure_is_critical(strings_en):
    ctx = make_context(dns_resolves=False)
    result = reachability.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL


def test_connection_error_is_critical(strings_en):
    ctx = make_context(dns_resolves=True, status_code=None, error="Connection refused")
    result = reachability.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL


def test_long_redirect_chain_is_warning(strings_en):
    ctx = make_context(
        dns_resolves=True,
        status_code=200,
        redirect_chain=["https://a.test", "https://b.test", "https://c.test"],
    )
    result = reachability.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_www_mismatch_is_warning(strings_en):
    ctx = make_context(dns_resolves=True, status_code=200, www_mismatch=True)
    result = reachability.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
