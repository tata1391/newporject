import json

import pytest

from app.database import JsonlEventLogger
from app.reports.models import ReportResult, ReportType, TestStatus as Status


@pytest.mark.asyncio
async def test_creates_jsonl_event(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    logger = JsonlEventLogger(path)
    await logger.log_report_result(
        "db-test",
        ReportResult(
            Status.SUCCESS,
            "TEST_TARGET",
            ReportType.OTHER,
            duration=0.42,
        ),
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["test_name"] == "db-test"
    assert event["status"] == "success"
    assert event["duration"] == 0.42


@pytest.mark.asyncio
async def test_sensitive_fields_are_redacted(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    logger = JsonlEventLogger(path)
    await logger.log_event(
        {
            "otp": "12345",
            "access_token": "abc",
            "nested": {"password": "secret", "safe": "ok"},
        }
    )
    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["otp"] == "[REDACTED]"
    assert event["access_token"] == "[REDACTED]"
    assert event["nested"]["password"] == "[REDACTED]"
    assert event["nested"]["safe"] == "ok"
