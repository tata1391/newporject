from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
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

@dataclass
class ReportRequest:
    target_id: str
    report_type: ReportType
    description: str = ""

@dataclass
class ReportResult:
    status: TestStatus
    target_id: str
    report_type: ReportType
    response_code: Optional[int] = None
    message: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    duration: Optional[float] = None

@dataclass
class SecurityTestResult:
    test_name: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    rate_limited: int = 0
    results: list[ReportResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful / self.total_requests) * 100
