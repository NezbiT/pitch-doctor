"""Shared HTML-parsing helpers used by more than one check."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

YEAR_RE = re.compile(r"(19|20)\d{2}")
PHONE_RE = re.compile(
    r"(\+?\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}"
)
ADDRESS_HINT_RE = re.compile(
    r"\b(street|st\.|avenue|ave\.|road|rd\.|calle|avenida|suite|ste\.|"
    r"boulevard|blvd\.?|p\.?o\.?\s?box)\b",
    re.IGNORECASE,
)


def soupify(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "html.parser")


def footer_text(soup: BeautifulSoup) -> str:
    footer = soup.find("footer")
    if footer is not None:
        return footer.get_text(" ", strip=True)
    # Fallback: some sites use a div with an id/class of "footer" instead of <footer>.
    candidate = soup.find(id=re.compile("footer", re.IGNORECASE))
    if candidate is None:
        candidate = soup.find(class_=re.compile("footer", re.IGNORECASE))
    if candidate is not None:
        return candidate.get_text(" ", strip=True)
    return ""


def latest_year_in_text(text: str) -> int | None:
    years = [int(m.group(0)) for m in YEAR_RE.finditer(text)]
    return max(years) if years else None


def has_viewport_meta(soup: BeautifulSoup) -> bool:
    tag = soup.find("meta", attrs={"name": "viewport"})
    return tag is not None and bool(tag.get("content"))


def has_tappable_phone_link(soup: BeautifulSoup) -> bool:
    return any(
        a.get("href", "").lower().startswith("tel:") for a in soup.find_all("a", href=True)
    )


def find_plain_text_phone(soup: BeautifulSoup) -> bool:
    body_text = soup.get_text(" ", strip=True)
    return bool(PHONE_RE.search(body_text))


def has_email_or_contact_link(soup: BeautifulSoup) -> bool:
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if href.startswith("mailto:") or "contact" in href:
            return True
    return False


def has_address_hint(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ", strip=True)
    if ADDRESS_HINT_RE.search(text):
        return True
    return soup.find(attrs={"itemtype": re.compile("PostalAddress", re.IGNORECASE)}) is not None


def has_title(soup: BeautifulSoup) -> bool:
    tag = soup.find("title")
    return tag is not None and bool(tag.get_text(strip=True))


def has_meta_description(soup: BeautifulSoup) -> bool:
    tag = soup.find("meta", attrs={"name": "description"})
    return tag is not None and bool(tag.get("content", "").strip())


def has_open_graph(soup: BeautifulSoup) -> bool:
    return soup.find("meta", attrs={"property": re.compile("^og:")}) is not None


def has_favicon(soup: BeautifulSoup) -> bool:
    return soup.find("link", rel=re.compile("icon", re.IGNORECASE)) is not None


def has_local_business_jsonld(soup: BeautifulSoup) -> bool:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if "LocalBusiness" in (script.string or "") or "localbusiness" in (
            script.string or ""
        ).lower():
            return True
    return False
