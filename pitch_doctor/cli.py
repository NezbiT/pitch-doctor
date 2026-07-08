"""pitch-doctor CLI: scan a website (or a batch of them) and generate a
client-ready, branded audit report.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pitch_doctor.checks.runner import build_scan_context, run_all_checks
from pitch_doctor.i18n import load_strings
from pitch_doctor.models import ScanReport
from pitch_doctor.report.builder import BrandInfo, write_report
from pitch_doctor.scoring import score_and_grade

app = typer.Typer(
    name="pitch-doctor",
    help="Turn any bad website into your next client.",
    add_completion=False,
)
console = Console()

_MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _format_date(lang: str) -> str:
    now = datetime.now(UTC)
    if lang == "es":
        return f"{now.day} de {_MONTHS_ES[now.month - 1]} de {now.year}"
    return now.strftime("%B %d, %Y")


def _lang_callback(value: str) -> str:
    if value not in ("en", "es"):
        raise typer.BadParameter("Language must be 'en' or 'es'.")
    return value


LangOption = typer.Option("en", "--lang", callback=_lang_callback, help="Report language: en or es.")
OutOption = typer.Option(Path("reports"), "--out", help="Output directory for reports.")
BrandNameOption = typer.Option("Your Agency", "--brand-name", help="Freelancer/agency name shown on the report.")
BrandEmailOption = typer.Option(None, "--brand-email", help="Freelancer contact email.")
BrandPhoneOption = typer.Option(None, "--brand-phone", help="Freelancer contact phone.")
BrandLogoOption = typer.Option(None, "--brand-logo", help="Path to a logo image for the report cover.")
JsonOption = typer.Option(False, "--json", help="Also dump raw findings as JSON.")
TimeoutOption = typer.Option(20.0, "--timeout", help="Per-site timeout in seconds.")
PdfOption = typer.Option(False, "--pdf", help="Also render a PDF using headless Chromium.")


async def _scan_one(url: str, lang: str, timeout: float) -> ScanReport:
    strings = load_strings(lang)
    ctx = await build_scan_context(url, timeout=timeout)
    checks = run_all_checks(ctx, strings)
    score, grade = score_and_grade(checks)
    return ScanReport(
        url=url,
        lang=lang,
        checks=checks,
        score=score,
        grade=grade,
        mobile_screenshot_b64=ctx.mobile_screenshot_b64,
        desktop_screenshot_b64=ctx.desktop_screenshot_b64,
        scanned_at=_format_date(lang),
        error=ctx.error,
    )


def _brand_from_options(name: str, email: str | None, phone: str | None, logo: Path | None) -> BrandInfo:
    return BrandInfo(name=name, email=email, phone=phone, logo_path=str(logo) if logo else None)


def _emit_report(scan: ScanReport, lang: str, out: Path, brand: BrandInfo, json_out: bool, pdf: bool) -> Path:
    strings = load_strings(lang)
    html_path = write_report(scan, strings, brand, out, pdf=pdf)
    if json_out:
        json_path = html_path.with_suffix(".json")
        json_path.write_text(
            json.dumps(
                {
                    "url": scan.url,
                    "score": scan.score,
                    "grade": scan.grade,
                    "checks": [c.to_dict() for c in scan.checks],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        console.print(strings.get("cli.json_written", path=str(json_path)))
    console.print(f"[green]{strings.get('cli.report_written', path=str(html_path))}[/green]")
    return html_path


@app.command()
def scan(
    url: str = typer.Argument(..., help="The website URL to audit."),
    lang: str = LangOption,
    out: Path = OutOption,
    brand_name: str = BrandNameOption,
    brand_email: str | None = BrandEmailOption,
    brand_phone: str | None = BrandPhoneOption,
    brand_logo: Path | None = BrandLogoOption,
    json_out: bool = JsonOption,
    timeout: float = TimeoutOption,
    pdf: bool = PdfOption,
) -> None:
    """Scan a single website and generate a client-ready audit report."""
    strings = load_strings(lang)
    brand = _brand_from_options(brand_name, brand_email, brand_phone, brand_logo)

    with console.status(strings.get("cli.scanning", url=url), spinner="dots"):
        scan_report = asyncio.run(_scan_one(url, lang, timeout))

    if scan_report.error:
        console.print(f"[yellow]{strings.get('cli.unreachable_error', url=url, detail=scan_report.error)}[/yellow]")

    console.print(strings.get("cli.scan_done", url=url, score=scan_report.score, grade=scan_report.grade))
    _emit_report(scan_report, lang, out, brand, json_out, pdf)


@app.command()
def batch(
    urls_file: Path = typer.Argument(..., help="Path to a text file with one URL per line."),
    lang: str = LangOption,
    out: Path = OutOption,
    brand_name: str = BrandNameOption,
    brand_email: str | None = BrandEmailOption,
    brand_phone: str | None = BrandPhoneOption,
    brand_logo: Path | None = BrandLogoOption,
    json_out: bool = JsonOption,
    timeout: float = TimeoutOption,
    pdf: bool = PdfOption,
) -> None:
    """Scan every URL in a file, continuing past failures, with a summary table at the end."""
    strings = load_strings(lang)
    brand = _brand_from_options(brand_name, brand_email, brand_phone, brand_logo)

    urls = [
        line.strip()
        for line in urls_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    results: list[tuple[str, ScanReport | None, str | None]] = []
    for url in urls:
        with console.status(strings.get("cli.scanning", url=url), spinner="dots"):
            try:
                scan_report = asyncio.run(_scan_one(url, lang, timeout))
            except Exception as exc:  # noqa: BLE001 -- one bad URL must not stop the batch
                results.append((url, None, str(exc)))
                console.print(f"[red]{url}: {exc}[/red]")
                continue

        if scan_report.error:
            console.print(
                f"[yellow]{strings.get('cli.unreachable_error', url=url, detail=scan_report.error)}[/yellow]"
            )
        _emit_report(scan_report, lang, out, brand, json_out, pdf)
        results.append((url, scan_report, None))

    table = Table(title=strings.get("cli.batch_summary_heading"))
    table.add_column("URL", overflow="fold")
    table.add_column("Score")
    table.add_column("Grade")
    table.add_column("Status")
    for url, scan_report, fatal_error in results:
        if scan_report is None:
            table.add_row(url, "-", "-", f"failed: {fatal_error}")
        elif scan_report.error:
            table.add_row(url, str(scan_report.score), scan_report.grade, "unreachable")
        else:
            table.add_row(url, str(scan_report.score), scan_report.grade, "ok")
    console.print(table)


if __name__ == "__main__":
    app()
