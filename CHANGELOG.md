# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
