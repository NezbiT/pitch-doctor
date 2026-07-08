from __future__ import annotations

from pitch_doctor.checks import contact_friction
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_tappable_phone_and_contact_is_ok(strings_en, good_html):
    ctx = make_context(html=good_html)
    result = contact_friction.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_plain_text_phone_is_critical(strings_en, bad_html):
    ctx = make_context(html=bad_html)
    result = contact_friction.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL


def test_missing_address_only_is_warning(strings_en):
    html = """
    <html><body>
      <p>Call us at <a href="tel:+15551234567">555-123-4567</a></p>
      <a href="mailto:hi@acme.test">hi@acme.test</a>
    </body></html>
    """
    ctx = make_context(html=html)
    result = contact_friction.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
