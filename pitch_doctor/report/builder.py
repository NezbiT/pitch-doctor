"""Renders a ScanReport into a self-contained HTML file, and optionally a PDF.

Design decision (documented in the README): WeasyPrint needs native GTK/Pango
libraries that are unreliable to install on Windows. Instead, the report is
always generated as a single self-contained HTML file (screenshots and any
logo are embedded as base64 data URIs, so it has zero external dependencies),
and ``--pdf`` renders that same HTML to PDF using the Chromium instance
Playwright already ships with (``page.pdf()``) -- no extra system packages.
"""

from __future__ import annotations

import base64
import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pitch_doctor.i18n import Strings
from pitch_doctor.models import ScanReport
from pitch_doctor.scoring import CHECK_WEIGHTS

TEMPLATE_DIR = Path(__file__).parent / "templates"

GRADE_COLORS = {
    "A": "#10b981",
    "B": "#10b981",
    "C": "#f59e0b",
    "D": "#ef4444",
    "F": "#ef4444",
}

SEVERITY_ORDER = {"critical": 0, "warning": 1, "ok": 2}


@dataclass
class BrandInfo:
    name: str = "Your Agency"
    email: str | None = None
    phone: str | None = None
    logo_path: str | None = None

    @property
    def logo_data_uri(self) -> str | None:
        if not self.logo_path:
            return None
        path = Path(self.logo_path)
        if not path.exists():
            return None
        ext = path.suffix.lstrip(".").lower() or "png"
        mime = "svg+xml" if ext == "svg" else ext
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/{mime};base64,{encoded}"


def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "jinja"]),
    )


def _report_strings(strings: Strings, scan: ScanReport, brand: BrandInfo) -> dict[str, str]:
    critical_count = sum(1 for c in scan.checks if c.severity.value == "critical")
    warning_count = sum(1 for c in scan.checks if c.severity.value == "warning")
    if critical_count or warning_count:
        summary_sentence = strings.get(
            "report.exec_summary_critical_sentence",
            critical=critical_count,
            warning=warning_count,
        )
    else:
        summary_sentence = strings.get("report.exec_summary_all_good_sentence")

    return {
        "tagline": strings.get("report.tagline"),
        "cover_report_title": strings.get("report.cover_report_title"),
        "cover_prepared_for": strings.get("report.cover_prepared_for"),
        "cover_prepared_by": strings.get("report.cover_prepared_by"),
        "cover_scanned_on": strings.get("report.cover_scanned_on", date=scan.scanned_at),
        "cover_health_score": strings.get("report.cover_health_score"),
        "cover_grade": strings.get("report.cover_grade"),
        "exec_summary_heading": strings.get("report.exec_summary_heading"),
        "exec_summary_intro": strings.get("report.exec_summary_intro"),
        "exec_summary_sentence": summary_sentence,
        "section_what_we_found": strings.get("report.section_what_we_found"),
        "section_why_it_matters": strings.get("report.section_why_it_matters"),
        "section_what_you_get": strings.get("report.section_what_you_get"),
        "section_mobile_view": strings.get("report.section_mobile_view"),
        "section_desktop_view": strings.get("report.section_desktop_view"),
        "severity_critical": strings.get("report.severity_critical"),
        "severity_warning": strings.get("report.severity_warning"),
        "severity_ok": strings.get("report.severity_ok"),
        "next_steps_heading": strings.get("report.next_steps_heading"),
        "next_steps_body": strings.get("report.next_steps_body"),
        "next_steps_cta": strings.get("report.next_steps_cta"),
        "footer_generated_by": strings.get("report.footer_generated_by", brand_name=brand.name),
        "toc_heading": strings.get("report.toc_heading"),
    }


def render_html(scan: ScanReport, strings: Strings, brand: BrandInfo) -> str:
    env = _get_env()
    template = env.get_template("report.html.jinja")

    checks_sorted = sorted(
        scan.checks, key=lambda c: SEVERITY_ORDER.get(c.severity.value, 3)
    )

    context = {
        "t": _report_strings(strings, scan, brand),
        "lang": scan.lang,
        "scan": scan,
        "checks": checks_sorted,
        "brand": brand,
        "brand_logo_data_uri": brand.logo_data_uri,
        "score": scan.score,
        "grade": scan.grade,
        "grade_color": GRADE_COLORS.get(scan.grade, "#10b981"),
        "cover_screenshot": scan.mobile_screenshot_b64,
        "generated_year": dt.datetime.now(dt.UTC).year,
        "check_weights": CHECK_WEIGHTS,
    }
    return template.render(**context)


def write_report(
    scan: ScanReport,
    strings: Strings,
    brand: BrandInfo,
    out_dir: Path,
    *,
    pdf: bool = False,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(scan.url)
    html = render_html(scan, strings, brand)
    html_path = out_dir / f"{slug}.html"
    html_path.write_text(html, encoding="utf-8")

    if pdf:
        pdf_path = out_dir / f"{slug}.pdf"
        _render_pdf(html_path, pdf_path)

    return html_path


def _slugify(url: str) -> str:
    cleaned = url.replace("https://", "").replace("http://", "")
    cleaned = cleaned.rstrip("/")
    return "".join(c if c.isalnum() or c in "-_." else "-" for c in cleaned)


def _render_pdf(html_path: Path, pdf_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        try:
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri())
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
        finally:
            browser.close()
