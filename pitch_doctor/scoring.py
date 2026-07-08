"""The pitch-doctor health-score formula.

Every check contributes a fixed point deduction depending on its severity.
Deductions are summed and subtracted from a perfect 100. This is intentionally
simple and transparent -- a freelancer reading the report (or its README)
should be able to reconstruct the number by hand.

    score = max(0, 100 - sum(deduction(check) for check in checks))

Weight table (points lost per check, by severity). "ok" always costs 0.
These weights roughly track how directly the issue costs the business
customers versus how much it merely looks unpolished.

+---------------------+----------+---------+
| check                | critical | warning |
+----------------------+----------+---------+
| load_speed           |    20    |   10    |
| ssl                  |    20    |   10    |
| reachability         |    15    |    8    |
| mobile_rendering     |    15    |    8    |
| outdated_signals     |    10    |    5    |
| broken_links         |    10    |    5    |
| contact_friction     |    10    |    5    |
| search_visibility    |    10    |    5    |
+----------------------+----------+---------+

Letter grades follow the usual US school scale:
A 90-100, B 80-89, C 70-79, D 60-69, F below 60.
"""

from __future__ import annotations

from pitch_doctor.models import CheckResult, Severity

CHECK_WEIGHTS: dict[str, dict[str, int]] = {
    "load_speed": {"critical": 20, "warning": 10},
    "ssl": {"critical": 20, "warning": 10},
    "reachability": {"critical": 15, "warning": 8},
    "mobile_rendering": {"critical": 15, "warning": 8},
    "outdated_signals": {"critical": 10, "warning": 5},
    "broken_links": {"critical": 10, "warning": 5},
    "contact_friction": {"critical": 10, "warning": 5},
    "search_visibility": {"critical": 10, "warning": 5},
}


def deduction_for(check: CheckResult) -> int:
    if check.severity == Severity.OK:
        return 0
    weights = CHECK_WEIGHTS.get(check.id, {"critical": 10, "warning": 5})
    return weights.get(check.severity.value, 0)


def compute_score(checks: list[CheckResult]) -> int:
    total_deduction = sum(deduction_for(c) for c in checks)
    return max(0, 100 - total_deduction)


def grade_for_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def score_and_grade(checks: list[CheckResult]) -> tuple[int, str]:
    score = compute_score(checks)
    return score, grade_for_score(score)
