# Bale Security Test Harness

A controlled Python test harness for validating Bale integrations without mass-reporting real users.

## Safety boundary

The project is designed for authorized testing, test accounts, and controlled environments. It intentionally limits request volume and keeps the actual Bale integration behind an adapter.

The current stage only establishes and validates the Aiobale connection/session lifecycle. It does not submit reports or perform bulk actions.

## Setup — Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and keep `TEST_MODE=true`.

## Stage 1 — connection check

The project pins the Enalite Aiobale release used by this adapter (`v0.1.5`). The current Aiobale documentation exposes `Client`/`Dispatcher` and a `start()` lifecycle; the adapter also supports a compatible `connect()` fallback.

Run:

```powershell
python main.py --check-connection
```

On the first run, Aiobale may start its normal authentication/session flow. Use only an account you own or are explicitly authorized to test. Do not paste phone numbers, OTP codes, session files, or tokens into GitHub or chat.

A successful check writes a structured event to `logs/events.jsonl` and then closes the client cleanly.

## Tests

```powershell
pytest
```

## Quality checks

```powershell
ruff check .
ruff format --check .
```

The repository follows a small-package layout with application code under `app/` and tests under `tests/`.
