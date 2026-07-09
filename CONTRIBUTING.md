# Contributing to pitch-doctor

Thanks for considering a contribution! This project is small on purpose --
please keep PRs focused.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
playwright install chromium  # skip if Google Chrome is already installed
```

## Before opening a PR

```bash
ruff check .
pytest
```

Both must pass. CI runs the same two commands.

## Adding or changing a check

Each check in `pitch_doctor/checks/` exposes a pure `evaluate(ctx, strings)`
function that takes a `ScanContext` and returns a `CheckResult` -- no network
or browser calls belong in that function. Put any new data-gathering logic in
`checks/runner.py` instead, so the check's decision logic stays unit-testable
with static HTML fixtures (see `tests/fixtures/`).

If you add a new check or change its copy, update **all four**
`pitch_doctor/i18n/{en,es,fr,zh}.json` files -- a test asserts they all have
identical key sets.

## Reporting bugs / suggesting features

Open a GitHub issue with the site (or a redacted example) that triggered it,
and what you expected to see instead.
