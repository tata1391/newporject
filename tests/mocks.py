from __future__ import annotations

import asyncio
from enum import Enum
import random

from app.reports.models import ReportRequest
from app.reports.service import RateLimitedError, SenderResponse


class MockScenario(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    RANDOM_RATE_LIMIT = "random_rate_limit"


class MockReportSender:
    """In-memory sender. It never imports aiobale and never contacts Bale."""

    def __init__(
        self,
        scenario: MockScenario = MockScenario.SUCCESS,
        *,
        rate_limit_after: int | None = None,
        timeout_seconds: float = 0.05,
        random_rate_limit_probability: float = 0.25,
        seed: int = 0,
    ) -> None:
        self.scenario = scenario
        self.rate_limit_after = rate_limit_after
        self.timeout_seconds = timeout_seconds
        self.random_rate_limit_probability = random_rate_limit_probability
        self.calls = 0
        self._rng = random.Random(seed)

    async def __call__(self, request: ReportRequest) -> SenderResponse:
        del request
        self.calls += 1

        if self.rate_limit_after is not None and self.calls > self.rate_limit_after:
            raise RateLimitedError("mock threshold reached")

        if self.scenario is MockScenario.SUCCESS:
            return SenderResponse(True, response_code=200, message="mock success")
        if self.scenario is MockScenario.FAILED:
            return SenderResponse(False, response_code=400, message="mock failure")
        if self.scenario is MockScenario.RATE_LIMITED:
            return SenderResponse(False, response_code=429, message="mock rate limit", rate_limited=True)
        if self.scenario is MockScenario.TIMEOUT:
            await asyncio.sleep(self.timeout_seconds)
            return SenderResponse(True, response_code=200, message="late mock success")
        if self.scenario is MockScenario.SERVER_ERROR:
            raise RuntimeError("mock server error")
        if self.scenario is MockScenario.RANDOM_RATE_LIMIT:
            if self._rng.random() < self.random_rate_limit_probability:
                raise RateLimitedError("mock random rate limit")
            return SenderResponse(True, response_code=200, message="mock success")
        raise AssertionError(f"unsupported mock scenario: {self.scenario}")


async def mock_report_sender(request: ReportRequest) -> SenderResponse:
    del request
    return SenderResponse(True, response_code=200, message="mock success")
