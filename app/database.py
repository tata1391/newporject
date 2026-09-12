from __future__ import annotations

import asyncio
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping

from app.reports.models import ReportResult, SecurityTestResult


_SENSITIVE_FRAGMENTS = (
    "otp",
    "password",
    "passcode",
    "token",
    "secret",
    "verification_code",
    "verificationcode",
    "session_key",
    "session_secret",
)
_REDACTED = "[REDACTED]"


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower().replace("-", "_")
    return any(fragment in lowered for fragment in _SENSITIVE_FRAGMENTS)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): (_REDACTED if _is_sensitive_key(str(key)) else _json_safe(item))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


class JsonlEventLogger:
    """Small async-safe JSONL event store for local test results."""

    def __init__(self, path: str | Path = "logs/events.jsonl") -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()

    async def log_event(self, event: Mapping[str, Any]) -> None:
        safe_event = _json_safe(dict(event))
        line = json.dumps(safe_event, ensure_ascii=False, separators=(",", ":"))
        async with self._lock:
            await asyncio.to_thread(self._append_line, line)

    def _append_line(self, line: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    async def log_report_result(self, test_name: str, result: ReportResult) -> None:
        await self.log_event(
            {
                "timestamp": result.created_at,
                "test_name": test_name,
                "status": result.status,
                "target_id": result.target_id,
                "report_type": result.report_type,
                "response_code": result.response_code,
                "message": result.message,
                "duration": result.duration,
            }
        )

    async def log_test_summary(self, summary: SecurityTestResult) -> None:
        await self.log_event(
            {
                "timestamp": summary.finished_at or summary.started_at,
                "event": "test_summary",
                "test_name": summary.test_name,
                "total_requests": summary.total_requests,
                "successful": summary.successful,
                "failed": summary.failed,
                "rate_limited": summary.rate_limited,
                "success_rate": summary.success_rate,
            }
        )
