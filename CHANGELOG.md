# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **The website is now optional.** `pitch-doctor scan` accepts
  `--business-name` and `--city` instead of a URL, so a business with no
  website -- usually the most valuable prospect -- can be audited. The 16
  website checks are then reported as *not applicable* at critical severity,
  keeping their full deduction (a business with no site has forfeited those
  points, not passed them) and collapsing into one report section instead of 16
  near-identical finding pages. `pitch-doctor scan https://example.com` and
  `batch` are unchanged.
- When a URL *is* given, the business name and city are inferred from the page's
  `LocalBusiness` JSON-LD, `og:site_name`, or `<title>`; anything passed
  explicitly wins.
- **Google Business Profile check** (`checks/google_business.py`): profile
  existence, category, published hours, photo count, review count and average
  rating, via the Google Places API (New). Uses field masking and a SQLite
  cache with a 30-day TTL to keep lookups cheap. Needs
  `GOOGLE_PLACES_API_KEY`; without it -- or on any API failure -- it reports an
  explicit unverified state that costs points but is never presented as a
  finding against the business, and never drives a recommendation. Owner
  replies to reviews are reported as a known blind spot: the Places API exposes
  no such field at any tier.
- **Social presence check** (`checks/social_presence.py`): Facebook/Instagram
  profiles linked from the site, probed anonymously. Nothing authenticates or
  scrapes past a login wall, so unconfirmable profiles are reported as
  *unverified* rather than as failures, and the worst outcome is a warning.
- Report CTA now maps findings to a starting point in a diagnostic tone: no
  website → Basic ($500), missing or thin Google listing → Growth, contact
  friction on an existing site → Professional ($1,000). All copy lives in
  `i18n/` so it can be edited without touching code.
- Web UI: the form requires the visitor's email before starting a scan and
  records the lead (email, business name, city, URL, score, timestamp) in
  `leads.db`. Web-layer only -- the scan engine never sees an email address and
  the CLI contract is untouched. Nothing is emailed yet.

### Changed
- Scoring gains two entries in the same deduction table: Google Business
  Profile at -12/-6 (Tier 1: for a local business the listing is often the only
  thing a nearby customer sees) and social presence at -4/-2 (lowest weight of
  all -- least verifiable, least consequential). All 18 checks at critical now
  sum to 145; the score still floors at 0.
- New i18n keys ship with complete **en** and **es**. `fr` and `zh` carry the
  English text as a placeholder so every language keeps an identical key set;
  translating them is open work.

### Fixed
- **A failing headless browser was reported as findings against the customer's
  site.** Playwright exceptions were caught and then dropped -- `ScanContext`
  had nowhere to put them -- leaving `load_time_seconds=None` and
  `viewport_meta_present=False`, which the checks read as facts. Every report
  from an affected deploy claimed the site was critically slow ("your site
  takes **N/As** to show anything on a phone") and had no mobile viewport tag,
  regardless of the site. Now:
  - `ScanContext.browser_error` carries the failure instead of discarding it,
    and the reason is printed in the evidence so it's diagnosable.
  - The viewport tag is read from the HTML already fetched over HTTP when the
    browser can't render, so it is never falsely reported missing.
  - Load speed distinguishes "the site never loaded" (a real critical finding,
    with its own copy -- no more `N/A` substitution) from "our browser failed"
    (a warning marked not-applicable, never blamed on the site).
  - Mobile rendering still calls out a genuinely missing viewport tag, but no
    longer claims anything about overflow it couldn't measure.
- **Docker: every scan lost its browser data.** The Playwright base image ships
  browsers for its own version while `pip install` resolved `playwright>=1.44.0`
  to a newer one, so Chromium's expected revision wasn't present and every
  launch failed. The image now runs `playwright install chromium` after pip.
- **Load speed measurement was reporting misleadingly high times.** It waited
  for the browser's full `load` event (which blocks on every slow
  third-party script, ad, or tracker) under an aggressive "Slow 4G" CDP
  throttle -- producing numbers far worse than what a real visitor on a
  normal connection experiences. Now measures First Contentful Paint (time
  until visible content appears) on a more realistic mid-range mobile
  throttle profile, and the report copy is explicit about the methodology.
- **The web scan endpoint returned 500 for malformed emails.** The email regex
  in `ScanRequest` had an unclosed group, so `re` raised `PatternError`, which
  pydantic does not convert to a 422. Fixed the pattern; invalid input is now a
  422 with a message.
- **The web UI page script was a syntax error.** A bad merge in
  `web/templates.py` left `const res = await // Safety check...`, so the whole
  page script failed to parse and the scan button did nothing.
- **PDF export failed hard when WeasyPrint's system libraries were missing.**
  WeasyPrint raises `OSError` (not `ImportError`) when Pango/GObject cannot be
  loaded; the fallback now catches both.
- **CRM lead API exposed all leads without authentication.** `crm-lead-api.py`
  bound to `0.0.0.0` with CORS `*` and a `POST` insert route. It now requires
  `CRM_API_TOKEN` (503 if unset, 401 if wrong), opens `leads.db` read-only,
  allows only `https://zerodigitx.com` by default, binds to localhost by default,
  and neutralises formula-like cells in the CSV export.
- Lint: removed an unused import and an unused variable in `web/app.py`, and the
  dead placeholder encoder/decoder pair it contained, so `ruff check .` passes.

### Added
- `pitch-doctor serve`: an optional local reactive web UI (`pip install -e
  ".[web]"`) -- paste a URL, watch live scan progress, get redirected to the
  finished report. Same scan engine as the CLI.
- French and Chinese report/CLI languages (`--lang fr|zh`), alongside
  English and Spanish -- all four fully externalized to `i18n/*.json`.

## [0.1.0] - 2026-07-07

### Added
- Initial release of `pitch-doctor`.
- `scan` and `batch` CLI commands built with Typer + Rich.
- 8 V1 checks: load speed, SSL/HTTPS, mobile rendering, outdated signals,
  broken links, contact friction, search visibility basics, and
  reachability/uptime.
- Health score formula (0-100) with A-F letter grades.
- Client-ready branded report generation: self-contained HTML by default,
  optional PDF via headless Chromium (`--pdf`).
- English and Spanish report/CLI copy (`--lang en|es`), fully externalized
  to `i18n/en.json` and `i18n/es.json`.
- Unit test suite (offline, fixture-based) for scoring and every check.
- GitHub Actions CI (ruff + pytest).
