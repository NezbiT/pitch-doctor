from __future__ import annotations

from pitch_doctor.checks import broken_links
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_no_broken_links_is_ok(strings_en):
    ctx = make_context(internal_links=["https://x.test/a", "https://x.test/b"], broken_links=[])
    result = broken_links.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_a_couple_broken_links_is_warning(strings_en):
    ctx = make_context(
        internal_links=["https://x.test/a", "https://x.test/b", "https://x.test/c"],
        broken_links=[("https://x.test/b", 404)],
    )
    result = broken_links.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_many_broken_links_is_critical(strings_en):
    ctx = make_context(
        internal_links=[f"https://x.test/{i}" for i in range(5)],
        broken_links=[(f"https://x.test/{i}", 404) for i in range(3)],
    )
    result = broken_links.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
    assert "3" in result.impact
