# Bale Security Test Harness

A controlled, async Python test harness for evaluating **report-system behaviour** such as success/failure handling, simulated rate limits, timeouts, session lifecycle, local logging, and connection/authentication behaviour around Bale Messenger.

> **Safety boundary:** this repository does **not** implement a real Bale report sender. All report-related execution paths use an injected mock sender. The Bale integration is limited to connection/session/handler lifecycle and identity probing for connection checks.

## Goals

- Keep report-behaviour logic independent from Bale internals.
- Simulate success, failure, rate limiting, timeout, and server errors locally.
- Enforce `TEST_MODE`, request-count caps, and inter-request delays.
- Persist test events as redacted JSONL.
- Reuse aiobale sessions without ever logging verification codes.
- Keep the code modular and unit-testable.

## Architecture

```text
                 +---------------------+
                 |       main.py       |
                 +----------+----------+
                            |
                   +--------+--------+
                   |                 |
                   v                 v
           +---------------+   +----------------+
           |   Handlers    |   | AiobaleAdapter |
           +-------+-------+   +--------+-------+
                   |                    |
                   v                    v
           +---------------+      +-----------+
           | ReportService |      |  aiobale  |
           +-------+-------+      +-----------+
                   |
           +-------+--------+
           |                |
           v                v
      Mock Sender       JSONL Logger
```

The `ReportTestService` knows only the `ReportSender` protocol. The shipped runtime sender and test senders are local mocks. No report RPC or report method exists in the repository.

## Requirements

- Python 3.11+
- `aiobale-py==0.3.8`
- `python-dotenv`
- `pytest`
- `pytest-asyncio`

The package name is `aiobale-py`, while imports use `aiobale`.

## Installation

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration

Copy the example file and edit only your local copy:

```powershell
Copy-Item .env.example .env
```

```env
BALE_SESSION_NAME=security_test_session
TEST_MODE=true
MAX_TEST_REQUESTS=10
REQUEST_DELAY=1.0
CONNECTION_TIMEOUT=20.0
```

`BALE_SESSION_NAME` is constrained to a plain file name so a configured session cannot escape `sessions/`. `.env`, session files, and generated logs are ignored by Git.

### Safety settings

- `TEST_MODE=false` blocks all report-behaviour tests before a sender is called.
- `MAX_TEST_REQUESTS` limits each test and also has a hard configuration cap of 100.
- `REQUEST_DELAY` cannot be negative.
- The `/test` handler always runs exactly **one** local mock request.
- There is no bulk-report command and no real-report implementation.

## Run the application

```powershell
python main.py
```

On first Bale authentication, aiobale handles the interactive phone/verification flow and writes its session. This project does not request, inspect, or log the verification code itself.

Available handlers:

- `/start` — harness information
- `/status` — local test/safety settings
- `/test` — one controlled mock scenario
- `/help` — command summary

## Connection check

```powershell
python main.py --check-connection
```

The connection check:

1. validates configuration,
2. constructs aiobale with the session path,
3. starts the client,
4. verifies authenticated connectivity with `get_me()`,
5. prints test-mode status,
6. cancels/closes the client,
7. performs **no report action**.

Typical output:

```text
================================
 Bale Security Test Harness
================================

[1] Loading configuration...
[2] Loading session...
[3] Connecting to Bale...
[4] Connection successful.
[5] Test mode: ENABLED
[6] No report action executed.

Connection check completed.
```

## Mock report system

`tests/mocks.py` implements these scenarios:

- `SUCCESS`
- `FAILED`
- `RATE_LIMITED`
- `TIMEOUT`
- `SERVER_ERROR`
- `RANDOM_RATE_LIMIT`

It can also emulate a deterministic threshold, for example five successful calls and a rate-limited sixth call:

```python
sender = MockReportSender(rate_limit_after=5)
```

The mock module never imports `aiobale` and never opens a network connection.

## Local JSONL logging

Events are written to:

```text
logs/events.jsonl
```

Example:

```json
{"timestamp":"2026-09-12T12:00:00+00:00","test_name":"handler_mock_test","status":"success","target_id":"TEST_TARGET","duration":0.0004}
```

Keys containing OTP/password/token/secret/verification/session-secret patterns are recursively replaced with `[REDACTED]` before serialization.

## Run tests

```powershell
pytest -q
```

All report tests are mock-only. Aiobale adapter tests use an in-memory fake client and do not contact Bale.

## Project structure

```text
bale_report_bot/
├── app/
│   ├── client/
│   │   ├── __init__.py
│   │   ├── bale_client.py
│   │   └── aiobale_adapter.py
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── models.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── bot_handlers.py
│   ├── __init__.py
│   ├── config.py
│   └── database.py
├── tests/
│   ├── __init__.py
│   ├── mocks.py
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_report_service.py
│   ├── test_handlers.py
│   ├── test_database.py
│   └── test_aiobale_adapter.py
├── sessions/.gitkeep
├── logs/.gitkeep
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
└── main.py
```

## Security notes and limitations

This harness is intentionally unsuitable for report abuse. It does not implement real report dispatch, user targeting, anti-abuse bypasses, rate-limit bypasses, session harvesting, multi-session abuse, or ban automation. Connection/authentication is the only real Bale integration.

Only run it with accounts and environments you own or are explicitly authorized to test. If a future legitimate lab requires integration beyond mocks, define the authorization boundary and isolated test target first, then review that integration separately rather than modifying the current mock sender in place.

## aiobale compatibility

The dependency is pinned to `aiobale-py==0.3.8`. Its documented construction/start contract is used directly:

```python
from aiobale import Client, Dispatcher

dp = Dispatcher()
client = Client(dp, session_file="sessions/security_test_session")
await client.start()
```

Because the public package quickstart documents construction/start but not a single canonical shutdown method, the wrapper cancels its tracked start task and then uses a shutdown hook only if the installed `Client` exposes one. This keeps cleanup explicit without assuming an undocumented method.
