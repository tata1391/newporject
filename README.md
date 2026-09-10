# Bale Security Test Harness

A controlled Python test harness for validating report-related integrations without mass-reporting real users.

## Safety boundary

The project is designed for authorized testing, test accounts, and controlled environments. It intentionally limits request volume and keeps the actual Bale integration behind an adapter.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and keep `TEST_MODE=true`.

## Tests

```bash
pytest
```

## Quality checks

```bash
ruff check .
ruff format --check .
```

The repository follows a small-package layout with application code under `app/` and tests under `tests/`.
