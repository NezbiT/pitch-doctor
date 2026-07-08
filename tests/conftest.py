from __future__ import annotations

from pathlib import Path

import pytest

from pitch_doctor.i18n import load_strings
from pitch_doctor.models import ScanContext

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture_html(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def make_context(**overrides) -> ScanContext:
    """Builds a ScanContext with sane, fully-offline defaults for check tests.

    Every field can be overridden via kwargs so each test only has to specify
    what it actually cares about.
    """
    defaults = dict(
        url="https://example-business.test",
        final_url="https://example-business.test",
        html="<html><body></body></html>",
        status_code=200,
        redirect_chain=[],
        headers={},
        load_time_seconds=1.2,
        has_valid_ssl=True,
        ssl_error=None,
        mobile_screenshot_b64=None,
        desktop_screenshot_b64=None,
        mobile_overflow_px=0,
        viewport_meta_present=True,
        internal_links=[],
        broken_links=[],
        dns_resolves=True,
        www_mismatch=False,
        timeout_seconds=20.0,
        error=None,
    )
    defaults.update(overrides)
    return ScanContext(**defaults)


@pytest.fixture
def strings_en():
    return load_strings("en")


@pytest.fixture
def strings_es():
    return load_strings("es")


@pytest.fixture
def good_html():
    return load_fixture_html("good_site.html")


@pytest.fixture
def bad_html():
    return load_fixture_html("bad_site.html")
