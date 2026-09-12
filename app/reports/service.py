from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
import time
from typing import Protocol

from app.database import JsonlEventLogger
from app.reports.models import (
    ReportRequest,
    ReportResult,
    SecurityTestResult,
    TestStatus,
    utc_now,
)


class ReportServiceError(RuntimeError):
    """Base error raised by the report test service."""


class TestModeDisabledError(ReportServiceError):
    """Sensitive test execution is blocked when TEST_MODE is disabled."""


class RequestLimitExceededError(ReportServiceError):
    """Raised when a test exceeds its configured request limit."""


class RateLimitedError(ReportServiceError):
    def __init__(self, message: str = "rate limited", *, response_code: int = 429) -> None:
        super().__init__(message)
        self.response_code = response_code


@dataclass(frozen=True, slots=True)
class SenderResponse:
    success: bool
    response_code: int | None = None
    message: str = ""
    rate_limited: bool = False


class ReportSender(Protocol):
    async def __call__(self, request: ReportRequest) -> SenderResponse: ...


class ReportTestService:
    """
    Executes bounded report-behaviour tests against an injected sender.

    The project intentionally ships only mock senders. There is no real Bale
    report implementation in this service or elsewhere in the repository.
    """

    def __init__(
        self,
        report_sender: ReportSender | Callable[[ReportRequest], Awaitable[SenderResponse]],
        *,
        test_mode: bool = True,
        max_test_requests: int = 10,
        request_delay: float = 1.0,
        request_timeout: float = 5.0,
        event_logger: JsonlEventLogger | None = None,
    ) -> None:
        if max_test_requests < 1:
            raise ValueError("max_test_requests must be >= 1")
        if request_delay < 0:
            raise ValueError("request_delay cannot be negative")
        if request_timeout <= 0:
            raise ValueError("request_timeout must be > 0")
        self._sender = report_sender
        self.test_mode = test_mode
        self.max_test_requests = max_test_requests
        self.request_delay = request_delay
        self.request_timeout = request_timeout
        self.event_logger = event_logger

    async def run_test(
        self,
        test_name: str,
        requests: Iterable[ReportRequest],
    ) -> SecurityTestResult:
        if not self.test_mode:
            raise TestModeDisabledError("TEST_MODE=false: report-behaviour tests are disabled")

        request_list = list(requests)
        if len(request_list) > self.max_test_requests:
            raise RequestLimitExceededError(
                f"test requested {len(request_list)} calls; limit is {self.max_test_requests}"
            )

        summary = SecurityTestResult(test_name=test_name)
        for index, request in enumerate(request_list):
            result = await self._run_one(request)
            summary.add_result(result)
            if self.event_logger is not None:
                await self.event_logger.log_report_result(test_name, result)

            if index < len(request_list) - 1 and self.request_delay:
                await asyncio.sleep(self.request_delay)

        summary.finished_at = utc_now()
        if self.event_logger is not None:
            await self.event_logger.log_test_summary(summary)
        return summary

    async def _run_one(self, request: ReportRequest) -> ReportResult:
        started = time.perf_counter()
        try:
            response = await asyncio.wait_for(
                self._sender(request), timeout=self.request_timeout
            )
            if response.rate_limited or response.response_code == 429:
                status = TestStatus.RATE_LIMITED
            elif response.success:
                status = TestStatus.SUCCESS
            else:
                status = TestStatus.FAILED
            return ReportResult(
                status=status,
                target_id=request.target_id,
                report_type=request.report_type,
                response_code=response.response_code,
                message=response.message,
                duration=time.perf_counter() - started,
            )
        except RateLimitedError as exc:
            return ReportResult(
                status=TestStatus.RATE_LIMITED,
                target_id=request.target_id,
                report_type=request.report_type,
                response_code=exc.response_code,
                message=str(exc),
                duration=time.perf_counter() - started,
            )
        except TimeoutError:
            return ReportResult(
                status=TestStatus.FAILED,
                target_id=request.target_id,
                report_type=request.report_type,
                message="request timeout",
                duration=time.perf_counter() - started,
            )
        except Exception as exc:  # noqa: BLE001 - intentional test harness boundary
            return ReportResult(
                status=TestStatus.FAILED,
                target_id=request.target_id,
                report_type=request.report_type,
                message=f"{type(exc).__name__}: {exc}",
                duration=time.perf_counter() - started,
            )
