"""Shared data types used across checks, scoring, and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    """The uniform output every check module produces.

    ``id`` must match a key under ``checks`` in the i18n string files.
    ``impact`` and ``name`` are already-localized, ready-to-render strings.
    """

    id: str
    name: str
    severity: Severity
    evidence: list[str]
    impact: str
    recommendation: str
    screenshots: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity.value,
            "evidence": self.evidence,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "screenshots": self.screenshots,
        }


@dataclass
class ScanContext:
    """Raw data gathered once per site and shared by every check.

    Keeping network/browser I/O here (and out of the check modules) is what
    lets check *decision logic* be unit tested with static HTML fixtures and
    no live network access.
    """

    url: str
    final_url: str
    html: str
    status_code: int | None
    redirect_chain: list[str]
    headers: dict[str, str]
    load_time_seconds: float | None
    has_valid_ssl: bool
    ssl_error: str | None
    mobile_screenshot_b64: str | None
    desktop_screenshot_b64: str | None
    mobile_overflow_px: int | None
    viewport_meta_present: bool
    internal_links: list[str]
    broken_links: list[tuple[str, int | str]]
    dns_resolves: bool
    www_mismatch: bool = False
    timeout_seconds: float = 20.0
    error: str | None = None


@dataclass
class ScanReport:
    url: str
    lang: str
    checks: list[CheckResult]
    score: int
    grade: str
    mobile_screenshot_b64: str | None = None
    desktop_screenshot_b64: str | None = None
    scanned_at: str = ""
    error: str | None = None
