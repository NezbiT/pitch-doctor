from __future__ import annotations

import pytest

from pitch_doctor.i18n import SUPPORTED_LANGUAGES, _load_raw


def _flatten_keys(node, prefix: str = "") -> set[str]:
    keys = set()
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key
            keys |= _flatten_keys(value, path)
    else:
        keys.add(prefix)
    return keys


def test_supports_four_languages():
    assert set(SUPPORTED_LANGUAGES) == {"en", "es", "fr", "zh"}


@pytest.mark.parametrize("lang", [lang for lang in SUPPORTED_LANGUAGES if lang != "en"])
def test_language_has_identical_key_set_to_english(lang):
    en_keys = _flatten_keys(_load_raw("en"))
    lang_keys = _flatten_keys(_load_raw(lang))
    assert lang_keys == en_keys


def test_every_check_has_name_impact_and_benefit():
    en = _load_raw("en")
    for check_id, entries in en["checks"].items():
        assert "name" in entries, check_id
        assert "impact_critical" in entries, check_id
        assert "impact_ok" in entries, check_id
        assert "benefit" in entries, check_id
