import pytest

from app.reports.models import ReportRequest, ReportType, TestStatus as Status
from app.reports.service import (
    ReportTestService,
    RequestLimitExceededError,
    TestModeDisabledError as ModeDisabledError,
)
from tests.mocks import MockReportSender, MockScenario


def req(index: int = 1) -> ReportRequest:
    return ReportRequest(f"TEST_TARGET_{index}", ReportType.OTHER)


@pytest.mark.asyncio
async def test_success() -> None:
    service = ReportTestService(MockReportSender(MockScenario.SUCCESS), request_delay=0)
    result = await service.run_test("success", [req()])
    assert result.successful == 1
    assert result.results[0].status is Status.SUCCESS
    assert result.results[0].duration is not None


@pytest.mark.asyncio
async def test_failure() -> None:
    service = ReportTestService(MockReportSender(MockScenario.FAILED), request_delay=0)
    result = await service.run_test("failure", [req()])
    assert result.failed == 1
    assert result.results[0].response_code == 400


@pytest.mark.asyncio
async def test_rate_limit() -> None:
    service = ReportTestService(
        MockReportSender(MockScenario.SUCCESS, rate_limit_after=5), request_delay=0
    )
    result = await service.run_test("rate-limit", [req(i) for i in range(1, 7)])
    assert result.successful == 5
    assert result.rate_limited == 1
    assert result.results[-1].status is Status.RATE_LIMITED


@pytest.mark.asyncio
async def test_sender_exception_is_recorded() -> None:
    service = ReportTestService(MockReportSender(MockScenario.SERVER_ERROR), request_delay=0)
    result = await service.run_test("exception", [req()])
    assert result.failed == 1
    assert "RuntimeError" in result.results[0].message


@pytest.mark.asyncio
async def test_timeout_is_recorded() -> None:
    service = ReportTestService(
        MockReportSender(MockScenario.TIMEOUT, timeout_seconds=0.05),
        request_delay=0,
        request_timeout=0.001,
    )
    result = await service.run_test("timeout", [req()])
    assert result.failed == 1
    assert "timeout" in result.results[0].message


@pytest.mark.asyncio
async def test_request_limit() -> None:
    service = ReportTestService(
        MockReportSender(), max_test_requests=2, request_delay=0
    )
    with pytest.raises(RequestLimitExceededError):
        await service.run_test("too-many", [req(1), req(2), req(3)])


@pytest.mark.asyncio
async def test_test_mode_blocks_execution() -> None:
    sender = MockReportSender()
    service = ReportTestService(sender, test_mode=False, request_delay=0)
    with pytest.raises(ModeDisabledError):
        await service.run_test("blocked", [req()])
    assert sender.calls == 0
