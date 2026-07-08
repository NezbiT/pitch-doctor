from __future__ import annotations

from pitch_doctor.checks.runner import _extract_internal_links, normalize_url


def test_normalize_url_adds_scheme():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_keeps_existing_scheme():
    assert normalize_url("http://example.com") == "http://example.com"


def test_extract_internal_links_filters_external_and_dedupes():
    html = """
    <html><body>
      <a href="/about">About</a>
      <a href="https://example.com/about">About again</a>
      <a href="https://external.test/other">External</a>
      <a href="mailto:hi@example.com">Email</a>
      <a href="#section">Anchor</a>
      <a href="/contact">Contact</a>
    </body></html>
    """
    links = _extract_internal_links(html, "https://example.com")
    assert links == ["https://example.com/about", "https://example.com/contact"]
