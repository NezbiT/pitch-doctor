from __future__ import annotations

from pitch_doctor.models import CheckResult, Severity
from pitch_doctor.scoring import compute_score, grade_for_score, score_and_grade


def _result(check_id: str, severity: Severity) -> CheckResult:
    return CheckResult(
        id=check_id,
        name=check_id,
        severity=severity,
        evidence=["evidence"],
        impact="impact",
        recommendation="benefit",
    )


def test_all_ok_scores_100():
    checks = [_result(cid, Severity.OK) for cid in ("load_speed", "ssl", "reachability")]
    assert compute_score(checks) == 100


def test_single_critical_deducts_its_weight():
    checks = [_result("ssl", Severity.CRITICAL)]
    # ssl critical weight is 20 points per the documented table.
    assert compute_score(checks) == 80


def test_score_never_goes_below_zero():
    checks = [
        _result("load_speed", Severity.CRITICAL),
        _result("ssl", Severity.CRITICAL),
        _result("reachability", Severity.CRITICAL),
        _result("mobile_rendering", Severity.CRITICAL),
        _result("outdated_signals", Severity.CRITICAL),
        _result("broken_links", Severity.CRITICAL),
        _result("contact_friction", Severity.CRITICAL),
        _result("search_visibility", Severity.CRITICAL),
    ]
    assert compute_score(checks) == 0


def test_grade_bands():
    assert grade_for_score(95) == "A"
    assert grade_for_score(85) == "B"
    assert grade_for_score(75) == "C"
    assert grade_for_score(65) == "D"
    assert grade_for_score(40) == "F"


def test_score_and_grade_combo():
    checks = [_result("load_speed", Severity.WARNING)]
    score, grade = score_and_grade(checks)
    assert score == 90
    assert grade == "A"
