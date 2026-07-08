# pitch-doctor

**Turn any bad website into your next client.**

[![License: MIT](https://img.shields.io/badge/license-MIT-10b981.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-10b981.svg)](pyproject.toml)
[![CI](https://github.com/pitch-doctor/pitch-doctor/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)

`pitch-doctor` is a CLI for web freelancers. Point it at a local business's
website and it produces a client-ready, plain-English audit report -- as a
polished PDF or standalone HTML file -- that you can send straight to the
business owner. No dev jargon. No Lighthouse-dump anxiety. Just "here's what's
costing you customers, and here's what fixing it gets you."

Scan it, brand it with your own name and contact info, send it, close the
deal.

## Demo

<!-- TODO: record a short terminal + report walkthrough GIF and drop it here -->
`![pitch-doctor demo](docs/demo.gif)`

## Install

```bash
pip install -e ".[dev]"
playwright install chromium  # skip this if you already have Google Chrome installed
```

(Published to PyPI as `pitch-doctor` once the first tag ships -- until then,
install from a checkout as above.)

By default pitch-doctor drives your system-installed Google Chrome
(Playwright's `channel="chrome"`) instead of downloading its own ~150 MB
Chromium bundle. If Chrome isn't installed, run `playwright install chromium`
and change `channel="chrome"` to plain `pw.chromium.launch()` in
`checks/runner.py` and `report/builder.py`.

## Usage

Scan a single site:

```bash
pitch-doctor scan https://example.com --lang en --out reports/
```

Scan a list of sites (one URL per line in `urls.txt`), continuing past any
failures, with a summary table at the end:

```bash
pitch-doctor batch urls.txt --lang es --out reports/
```

Brand the report as your own agency's deliverable:

```bash
pitch-doctor scan https://example.com \
  --brand-name "Acme Web Studio" \
  --brand-email hello@acmewebstudio.com \
  --brand-phone "+1 555 010 2020" \
  --brand-logo ./logo.png \
  --pdf
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `--lang` | `en` | Report/CLI language: `en` or `es` |
| `--out` | `reports/` | Output directory |
| `--brand-name` | `Your Agency` | Name shown on the report cover and CTA |
| `--brand-email` | _(none)_ | Contact email on the final CTA page |
| `--brand-phone` | _(none)_ | Contact phone on the final CTA page |
| `--brand-logo` | _(none)_ | Path to a logo image for the cover |
| `--json` | off | Also dump raw findings as JSON next to the report |
| `--timeout` | `20` | Per-site timeout, in seconds |
| `--pdf` | off | Also render a PDF (via headless Chromium) alongside the HTML report |

### Sample report

<!-- TODO: replace with an actual screenshot of examples/example.com.html once you have one you like -->
`![sample report cover](docs/sample-report-cover.png)`

A generated example lives in [`examples/`](examples/) after you run the scan
described below.

## The checks (V1)

Each check returns a severity (`critical` / `warning` / `ok`), the evidence
that led to it, and a business-language explanation of why it matters:

1. **Load speed** -- mobile load time via Playwright navigation timing on a simulated mobile connection.
2. **SSL / HTTPS** -- missing HTTPS or an invalid certificate.
3. **Mobile rendering** -- viewport meta tag, horizontal overflow, and side-by-side phone + desktop screenshots.
4. **Outdated signals** -- stale copyright year in the footer.
5. **Broken links** -- up to 25 internal links checked concurrently for 404s.
6. **Contact friction** -- phone numbers not wrapped in `tel:` links, missing email/contact link, missing address.
7. **Search visibility basics** -- title, meta description, Open Graph tags, favicon, `LocalBusiness` JSON-LD.
8. **Reachability / uptime** -- DNS resolution, response status, redirect chain length, www/non-www consistency.

## The health score

Every check starts from a perfect site (100 points) and loses points based on
its severity. The formula is intentionally simple enough to reconstruct by
hand from the report:

```
score = max(0, 100 - sum(deduction(check) for check in checks))
```

| Check | Critical | Warning |
|---|---|---|
| Load speed | -20 | -10 |
| SSL / HTTPS | -20 | -10 |
| Reachability / uptime | -15 | -8 |
| Mobile rendering | -15 | -8 |
| Outdated signals | -10 | -5 |
| Broken links | -10 | -5 |
| Contact friction | -10 | -5 |
| Search visibility basics | -10 | -5 |

An `ok` result always costs 0. Letter grades: **A** 90-100, **B** 80-89,
**C** 70-79, **D** 60-69, **F** below 60. See `pitch_doctor/scoring.py` for
the implementation.

## Why HTML by default, and PDF as a flag

WeasyPrint (the usual Python-to-PDF route) depends on native GTK/Pango
libraries that are painful to install reliably on Windows. Rather than fight
that, every report is generated as a single self-contained HTML file first
(screenshots and any logo are embedded as base64 data URIs -- no external
assets, opens offline, emails cleanly as an attachment). Pass `--pdf` to also
render that same HTML to PDF using the headless Chromium instance Playwright
already ships with (`page.pdf()`) -- no extra system dependencies required.

## Project layout

```
pitch_doctor/
  cli.py              Typer app: scan / batch commands
  models.py            CheckResult, ScanContext, ScanReport
  scoring.py            Health score formula
  checks/               One module per check (pure decision logic) + runner.py (I/O)
  report/               Jinja2 template + HTML/PDF builder
  i18n/                 en.json / es.json -- all report and CLI copy
tests/                  Offline unit tests with static HTML fixtures
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: `ruff check .` and
`pytest` must both pass before opening a PR, and check logic must stay
network-free and unit-testable.

## License

MIT -- see [LICENSE](LICENSE).

---

## Español: inicio rápido

`pitch-doctor` es una CLI para freelancers web: analiza el sitio de un
negocio local y genera un reporte de auditoría listo para el cliente, en
lenguaje de negocio (no de programador), como PDF o HTML.

**Instalación:**

```bash
pip install -e ".[dev]"
playwright install chromium
```

**Analizar un sitio:**

```bash
pitch-doctor scan https://ejemplo.com --lang es --out reportes/
```

**Analizar una lista de sitios** (un URL por línea en `urls.txt`, continúa
aunque algunos fallen, con una tabla resumen al final):

```bash
pitch-doctor batch urls.txt --lang es --out reportes/
```

Usa `--brand-name`, `--brand-email`, `--brand-phone` y `--brand-logo` para
poner tu propia marca en el reporte, y `--pdf` para generar también un PDF.
