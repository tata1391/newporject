from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ReportType(str, Enum):
    INVALID = "invalid"
    SPAM = "spam"
    ABUSE = "abuse"
    OTHER = "other"


class TestStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ReportRequest:
    target_id: str
    report_type: ReportType
    description: str = ""

    def __post_init__(self) -> None:
        self.target_id = self.target_id.strip()
        if not self.target_id:
            raise ValueError("target_id cannot be empty")


@dataclass(slots=True)
class ReportResult:
    status: TestStatus
    target_id: str
    report_type: ReportType
    response_code: Optional[int] = None
    message: str = ""
    created_at: datetime = field(default_factory=utc_now)
    duration: Optional[float] = None


@dataclass(slots=True)
class SecurityTestResult:
    test_name: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    rate_limited: int = 0
    results: list[ReportResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=utc_now)
    finished_at: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful / self.total_requests) * 100.0

    def add_result(self, result: ReportResult) -> None:
        self.results.append(result)
        self.total_requests += 1
        if result.status is TestStatus.SUCCESS:
            self.successful += 1
        elif result.status is TestStatus.RATE_LIMITED:
            self.rate_limited += 1
        elif result.status is TestStatus.FAILED:
            self.failed += 1
