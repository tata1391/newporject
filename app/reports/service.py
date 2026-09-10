import asyncio
import time
from typing import Callable, Awaitable
from app.config import settings
from app.reports.models import ReportRequest, ReportResult, SecurityTestResult, TestStatus

class ReportTestService:
    """Controlled report-security test service."""

    def __init__(self, report_sender: Callable[[ReportRequest], Awaitable[ReportResult]]):
        self.report_sender = report_sender

    async def test_single_report(self, request: ReportRequest) -> ReportResult:
        started = time.perf_counter()
        try:
            result = await self.report_sender(request)
        except Exception as exc:
            result = ReportResult(
                status=TestStatus.FAILED,
                target_id=request.target_id,
                report_type=request.report_type,
                message=str(exc),
            )
        result.duration = time.perf_counter() - started
        return result

    async def run_test(self, test_name: str, requests: list[ReportRequest]) -> SecurityTestResult:
        if not settings.test_mode:
            raise RuntimeError("اجرای تست فقط در TEST_MODE امکان‌پذیر است.")
        if len(requests) > settings.max_test_requests:
            raise ValueError(f"تعداد درخواست‌ها نمی‌تواند بیشتر از {settings.max_test_requests} باشد.")

        test_result = SecurityTestResult(test_name=test_name)
        for request in requests:
            result = await self.test_single_report(request)
            test_result.total_requests += 1
            test_result.results.append(result)

            if result.status == TestStatus.SUCCESS:
                test_result.successful += 1
            elif result.status == TestStatus.RATE_LIMITED:
                test_result.rate_limited += 1
            else:
                test_result.failed += 1

            if settings.request_delay > 0:
                await asyncio.sleep(settings.request_delay)

        from datetime import datetime
        test_result.finished_at = datetime.utcnow()
        return test_result
