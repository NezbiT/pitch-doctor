from __future__ import annotations

from pitch_doctor.i18n import _load_raw


def _flatten_keys(node, prefix: str = "") -> set[str]:
    keys = set()
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key
            keys |= _flatten_keys(value, path)
    else:
        keys.add(prefix)
    return keys


def test_en_and_es_have_identical_key_sets():
    en_keys = _flatten_keys(_load_raw("en"))
    es_keys = _flatten_keys(_load_raw("es"))
    assert en_keys == es_keys


def test_every_check_has_name_impact_and_benefit():
    en = _load_raw("en")
    for check_id, entries in en["checks"].items():
        assert "name" in entries, check_id
        assert "impact_critical" in entries, check_id
        assert "impact_ok" in entries, check_id
        assert "benefit" in entries, check_id
