"""Loads localized report/CLI strings from en.json / es.json.

No report or CLI copy is hardcoded in Python -- everything user-facing lives
in these two JSON files so a translator can add a new language without
touching code.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

_I18N_DIR = Path(__file__).parent
SUPPORTED_LANGUAGES = ("en", "es")
DEFAULT_LANGUAGE = "en"


@cache
def _load_raw(lang: str) -> dict[str, Any]:
    path = _I18N_DIR / f"{lang}.json"
    if not path.exists():
        raise ValueError(f"Unsupported language: {lang!r}")
    return json.loads(path.read_text(encoding="utf-8"))


class Strings:
    """Thin accessor over a language's string tree with dotted-path lookup."""

    def __init__(self, lang: str):
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE
        self.lang = lang
        self._data = _load_raw(lang)

    def get(self, dotted_path: str, **kwargs: object) -> str:
        node: Any = self._data
        for part in dotted_path.split("."):
            if not isinstance(node, dict) or part not in node:
                raise KeyError(f"Missing i18n key: {dotted_path!r} for lang={self.lang!r}")
            node = node[part]
        if not isinstance(node, str):
            raise KeyError(f"i18n key {dotted_path!r} does not resolve to a string")
        return node.format(**kwargs) if kwargs else node

    def check_name(self, check_id: str) -> str:
        return self.get(f"checks.{check_id}.name")

    def check_text(self, check_id: str, kind: str, **kwargs: object) -> str:
        """kind is one of: impact, found, benefit (impact/found take a severity suffix)."""
        return self.get(f"checks.{check_id}.{kind}", **kwargs)


def load_strings(lang: str) -> Strings:
    return Strings(lang)
