"""Validation rules for the web form's scan request.

Skipped entirely when the ``web`` extra isn't installed -- CI installs only
``[dev]``, so importing FastAPI at module scope would break it.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from pydantic import ValidationError  # noqa: E402

from pitch_doctor.web.app import (  # noqa: E402
    ScanRequest,
    _encode_report_filename_v2,
    _resolve_signed_report,
)


def _payload(**overrides):
    base = {
        "url": "https://joesplumbing.test",
        "email": "owner@example.test",
        "brand_name": "Joe's Plumbing",
        "brand_phone": "281-000-0000",
    }
    base.update(overrides)
    return base


def test_a_separate_contact_email_is_no_longer_required():
    # The public form asks once. A visitor auditing their own business would
    # only have typed the same address twice.
    req = ScanRequest(**_payload())
    assert req.brand_email is None
    assert req.email == "owner@example.test"


def test_a_distinct_contact_email_is_still_accepted():
    # A freelancer branding the report as their agency still wants them apart.
    req = ScanRequest(**_payload(brand_email="hello@acmewebstudio.test"))
    assert req.brand_email == "hello@acmewebstudio.test"
    assert req.email == "owner@example.test"


def test_the_lead_email_is_still_required():
    with pytest.raises(ValidationError):
        ScanRequest(**{k: v for k, v in _payload().items() if k != "email"})


def test_a_malformed_lead_email_is_rejected():
    with pytest.raises(ValidationError):
        ScanRequest(**_payload(email="not-an-email"))


def test_a_business_without_a_website_still_needs_a_city():
    with pytest.raises(ValidationError):
        ScanRequest(**_payload(url=None, business_name="Joe's Plumbing"))


def test_a_business_name_and_city_stand_in_for_a_url():
    req = ScanRequest(**_payload(url=None, business_name="Joe's Plumbing", city="Houston"))
    assert req.url is None
    assert req.business_name == "Joe's Plumbing"


def test_signed_report_url_serves_the_copied_file(tmp_path):
    original = tmp_path / "example.com-es.html"
    original.write_text("<html>ok</html>", encoding="utf-8")
    signed_name = _encode_report_filename_v2(original.name)
    (tmp_path / signed_name).write_bytes(original.read_bytes())

    resolved = _resolve_signed_report(tmp_path, signed_name)
    assert resolved is not None
    assert resolved.read_text(encoding="utf-8") == "<html>ok</html>"
