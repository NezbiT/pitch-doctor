"""Shared Playwright Chromium launch options for CLI + web UI.

Local default uses the system Google Chrome install (channel=chrome).
In Docker/cloud set:

  PLAYWRIGHT_CHANNEL=chromium   # use Playwright's bundled browser
  PLAYWRIGHT_NO_SANDBOX=1       # required in most containers
"""

from __future__ import annotations

import os
from typing import Any


def chromium_launch_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    channel = os.getenv("PLAYWRIGHT_CHANNEL", "chrome").strip().lower()
    if channel and channel not in ("chromium", "none", "bundled", "default"):
        kwargs["channel"] = channel

    if os.getenv("PLAYWRIGHT_NO_SANDBOX", "").strip().lower() in ("1", "true", "yes"):
        kwargs["args"] = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ]
    return kwargs
