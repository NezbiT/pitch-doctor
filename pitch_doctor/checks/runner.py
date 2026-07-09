"""Gathers all raw data (network + browser) into a ScanContext, then runs
every check's pure ``evaluate`` function against it.

This is the only module in the package that touches the network or a real
browser -- keeping it isolated is what makes every check's decision logic
testable offline with static HTML fixtures.
"""

from __future__ import annotations

import asyncio
import base64
import socket
import time
from collections.abc import Callable
from urllib.parse import urljoin, urlparse

import httpx
from playwright.async_api import Browser, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from pitch_doctor.checks import ALL_CHECKS
from pitch_doctor.checks.base import soupify
from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 pitch-doctor/0.1"
)
MOBILE_VIEWPORT = {"width": 390, "height": 844}
DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
MAX_LINKS_TO_CHECK = 25
LINK_CHECK_CONCURRENCY = 8

# A representative mid-range mobile connection (roughly "Regular 4G"), not a
# worst-case one. Earlier versions throttled to Lighthouse's aggressive "Slow
# 4G" profile (1.6 Mbps / 150ms latency) *and* waited for the browser's full
# "load" event -- which blocks on every slow third-party script, ad, or
# tracker. That combination produced numbers far worse than what a real
# visitor on a decent connection actually experiences, since real visitors
# perceive "loaded" when content paints, not when the last analytics beacon
# finishes. We now throttle more realistically and measure First Contentful
# Paint (see PAINT_TIMING_JS below) instead of the full load event.
NETWORK_CONDITIONS = {
    "offline": False,
    "downloadThroughput": 4 * 1024 * 1024 / 8,
    "uploadThroughput": 1.5 * 1024 * 1024 / 8,
    "latency": 40,
}

# Reads the Paint Timing / Navigation Timing APIs from inside the page.
# first-contentful-paint is what most closely matches a real visitor's sense
# of "the page loaded" -- it fires when the browser paints the first text,
# image, or non-white content, regardless of slow-loading background scripts.
PAINT_TIMING_JS = """() => {
    const nav = performance.getEntriesByType('navigation')[0];
    const paint = performance.getEntriesByType('paint').find(
        (e) => e.name === 'first-contentful-paint'
    );
    return {
        fcp: paint ? paint.startTime : null,
        domContentLoaded: nav ? nav.domContentLoadedEventEnd : null,
    };
}"""

FCP_POLL_INTERVAL_SECONDS = 0.25
FCP_MAX_WAIT_SECONDS = 5.0


def normalize_url(url: str) -> str:
    if not urlparse(url).scheme:
        return f"https://{url}"
    return url


def _resolves_dns(hostname: str) -> bool:
    try:
        socket.getaddrinfo(hostname, None)
        return True
    except socket.gaierror:
        return False


def _same_site(base_netloc: str, candidate: str) -> bool:
    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https", ""):
        return False
    candidate_netloc = parsed.netloc.lower().removeprefix("www.")
    return candidate_netloc in ("", base_netloc)


def _extract_internal_links(html: str, base_url: str) -> list[str]:
    soup = soupify(html)
    base_netloc = urlparse(base_url).netloc.lower().removeprefix("www.")
    seen: set[str] = set()
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        if not _same_site(base_netloc, absolute) or absolute in seen:
            continue
        seen.add(absolute)
        links.append(absolute)
        if len(links) >= MAX_LINKS_TO_CHECK:
            break
    return links


async def _check_link(client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore) -> tuple[str, int | str] | None:
    async with sem:
        try:
            resp = await client.head(url, follow_redirects=True)
            if resp.status_code == 405:
                resp = await client.get(url, follow_redirects=True)
            if resp.status_code >= 400:
                return url, resp.status_code
            return None
        except httpx.HTTPError:
            return url, "error"


async def _check_broken_links(links: list[str], timeout: float) -> list[tuple[str, int | str]]:
    if not links:
        return []
    sem = asyncio.Semaphore(LINK_CHECK_CONCURRENCY)
    async with httpx.AsyncClient(
        timeout=timeout, headers={"User-Agent": USER_AGENT}, verify=False
    ) as client:
        results = await asyncio.gather(*(_check_link(client, link, sem) for link in links))
    return [r for r in results if r is not None]


async def _check_www_mismatch(url: str, timeout: float) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc
    if host.startswith("www."):
        alt_host = host.removeprefix("www.")
    else:
        alt_host = f"www.{host}"
    alt_url = parsed._replace(netloc=alt_host).geturl()
    try:
        async with httpx.AsyncClient(
            timeout=timeout, headers={"User-Agent": USER_AGENT}, verify=False, follow_redirects=True
        ) as client:
            primary = await client.get(url)
            alt = await client.get(alt_url)
            primary_domain = urlparse(str(primary.url)).netloc.lower().removeprefix("www.")
            alt_domain = urlparse(str(alt.url)).netloc.lower().removeprefix("www.")
            primary_ok = primary.status_code < 400
            alt_broken = alt.status_code >= 400
            return (primary_ok and alt_broken) or primary_domain != alt_domain
    except httpx.HTTPError:
        return False


async def _fetch_http(url: str, timeout: float) -> dict:
    """Fetch the page over HTTP(S), tolerating -- and recording -- SSL failures."""
    headers = {"User-Agent": USER_AGENT}
    ssl_error: str | None = None
    has_valid_ssl = url.startswith("https://")
    try:
        async with httpx.AsyncClient(
            timeout=timeout, headers=headers, follow_redirects=True
        ) as client:
            resp = await client.get(url)
    except httpx.ConnectError as exc:
        if has_valid_ssl and ("certificate" in str(exc).lower() or "ssl" in str(exc).lower()):
            ssl_error = str(exc)
            has_valid_ssl = False
            try:
                async with httpx.AsyncClient(
                    timeout=timeout, headers=headers, follow_redirects=True, verify=False
                ) as insecure_client:
                    resp = await insecure_client.get(url)
            except httpx.HTTPError as inner_exc:
                return {"error": str(inner_exc)}
        else:
            return {"error": str(exc)}
    except httpx.HTTPError as exc:
        return {"error": str(exc)}

    return {
        "status_code": resp.status_code,
        "final_url": str(resp.url),
        "redirect_chain": [str(r.url) for r in resp.history],
        "headers": dict(resp.headers),
        "html": resp.text,
        "has_valid_ssl": has_valid_ssl,
        "ssl_error": ssl_error,
    }


async def _capture_browser_signals(url: str, timeout: float) -> dict:
    result = {
        "load_time_seconds": None,
        "mobile_screenshot_b64": None,
        "desktop_screenshot_b64": None,
        "mobile_overflow_px": None,
        "viewport_meta_present": False,
    }
    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(channel="chrome")
        try:
            mobile_context = await browser.new_context(
                viewport=MOBILE_VIEWPORT,
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
                ),
                is_mobile=True,
                has_touch=True,
            )
            page = await mobile_context.new_page()
            cdp = await mobile_context.new_cdp_session(page)
            await cdp.send("Network.enable")
            await cdp.send("Network.emulateNetworkConditions", NETWORK_CONDITIONS)

            start = time.perf_counter()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            except PlaywrightTimeoutError:
                pass  # still try to read whatever painted and screenshot it below

            fcp_seconds: float | None = None
            timing: dict = {}
            deadline = time.perf_counter() + min(FCP_MAX_WAIT_SECONDS, timeout)
            while time.perf_counter() < deadline:
                timing = await page.evaluate(PAINT_TIMING_JS)
                if timing.get("fcp") is not None:
                    fcp_seconds = timing["fcp"] / 1000
                    break
                await asyncio.sleep(FCP_POLL_INTERVAL_SECONDS)

            if fcp_seconds is None and timing.get("domContentLoaded") is not None:
                fcp_seconds = timing["domContentLoaded"] / 1000
            if fcp_seconds is None:
                fcp_seconds = time.perf_counter() - start
            result["load_time_seconds"] = fcp_seconds

            result["viewport_meta_present"] = await page.evaluate(
                "() => !!document.querySelector('meta[name=\"viewport\"]')"
            )
            result["mobile_overflow_px"] = await page.evaluate(
                "() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth)"
            )
            screenshot = await page.screenshot(full_page=False)
            result["mobile_screenshot_b64"] = base64.b64encode(screenshot).decode("ascii")
            await mobile_context.close()

            desktop_context = await browser.new_context(viewport=DESKTOP_VIEWPORT)
            desktop_page = await desktop_context.new_page()
            try:
                await desktop_page.goto(url, wait_until="load", timeout=timeout * 1000)
            except PlaywrightTimeoutError:
                pass  # best-effort screenshot of whatever rendered
            desktop_screenshot = await desktop_page.screenshot(full_page=False)
            result["desktop_screenshot_b64"] = base64.b64encode(desktop_screenshot).decode("ascii")
            await desktop_context.close()
        finally:
            await browser.close()
    return result


async def build_scan_context(
    url: str,
    timeout: float = 20.0,
    on_progress: Callable[[str], None] | None = None,
) -> ScanContext:
    """Gathers a ScanContext. ``on_progress``, if given, is called synchronously
    with one of: "dns", "http", "browser", "links" as each stage starts --
    used by the web UI to show live scan progress.
    """

    def notify(stage: str) -> None:
        if on_progress is not None:
            on_progress(stage)

    url = normalize_url(url)
    hostname = urlparse(url).netloc.split(":")[0]
    notify("dns")
    dns_resolves = await asyncio.to_thread(_resolves_dns, hostname)

    notify("http")
    http_data = await _fetch_http(url, timeout) if dns_resolves else {"error": "DNS resolution failed"}

    html = http_data.get("html", "")
    final_url = http_data.get("final_url", url)

    browser_signals: dict = {
        "load_time_seconds": None,
        "mobile_screenshot_b64": None,
        "desktop_screenshot_b64": None,
        "mobile_overflow_px": None,
        "viewport_meta_present": False,
    }
    if dns_resolves and not http_data.get("error"):
        notify("browser")
        try:
            browser_signals = await _capture_browser_signals(url, timeout)
        except Exception as exc:  # noqa: BLE001 -- a browser failure must not abort the scan
            browser_signals["error"] = str(exc)

    internal_links = _extract_internal_links(html, final_url) if html else []
    broken_links, www_mismatch = ([], False)
    if dns_resolves and not http_data.get("error"):
        notify("links")
        broken_links, www_mismatch = await asyncio.gather(
            _check_broken_links(internal_links, timeout),
            _check_www_mismatch(final_url, timeout),
        )

    return ScanContext(
        url=url,
        final_url=final_url,
        html=html,
        status_code=http_data.get("status_code"),
        redirect_chain=http_data.get("redirect_chain", []),
        headers=http_data.get("headers", {}),
        load_time_seconds=browser_signals.get("load_time_seconds"),
        has_valid_ssl=http_data.get("has_valid_ssl", False),
        ssl_error=http_data.get("ssl_error"),
        mobile_screenshot_b64=browser_signals.get("mobile_screenshot_b64"),
        desktop_screenshot_b64=browser_signals.get("desktop_screenshot_b64"),
        mobile_overflow_px=browser_signals.get("mobile_overflow_px"),
        viewport_meta_present=browser_signals.get("viewport_meta_present", False),
        internal_links=internal_links,
        broken_links=broken_links,
        dns_resolves=dns_resolves,
        www_mismatch=www_mismatch,
        timeout_seconds=timeout,
        error=http_data.get("error"),
    )


def run_all_checks(ctx: ScanContext, strings: Strings) -> list[CheckResult]:
    return [module.evaluate(ctx, strings) for module in ALL_CHECKS]
