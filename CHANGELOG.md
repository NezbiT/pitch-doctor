# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- **Load speed measurement was reporting misleadingly high times.** It waited
  for the browser's full `load` event (which blocks on every slow
  third-party script, ad, or tracker) under an aggressive "Slow 4G" CDP
  throttle -- producing numbers far worse than what a real visitor on a
  normal connection experiences. Now measures First Contentful Paint (time
  until visible content appears) on a more realistic mid-range mobile
  throttle profile, and the report copy is explicit about the methodology.

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
