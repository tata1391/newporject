import pytest

from app.reports.models import ReportRequest, ReportResult, ReportType, TestStatus
from app.reports.service import ReportTestService


@pytest.mark.asyncio
async def test_run_test_with_fake_sender() -> None:
    async def fake_sender(request: ReportRequest) -> ReportResult:
        return ReportResult(
            status=TestStatus.SUCCESS,
            target_id=request.target_id,
            report_type=request.report_type,
            message="simulated",
        )

    service = ReportTestService(fake_sender)
    result = await service.run_test(
        "fake",
        [ReportRequest("test-1", ReportType.OTHER)],
    )

    assert result.total_requests == 1
    assert result.successful == 1
    assert result.failed == 0
    assert result.success_rate == 100.0


@pytest.mark.asyncio
async def test_sender_exception_becomes_failed_result() -> None:
    async def failing_sender(request: ReportRequest) -> ReportResult:
        raise RuntimeError("simulated failure")

    service = ReportTestService(failing_sender)
    result = await service.run_test(
        "failure",
        [ReportRequest("test-1", ReportType.OTHER)],
    )

    assert result.failed == 1
    assert result.results[0].status == TestStatus.FAILED
    assert "simulated failure" in result.results[0].message


@pytest.mark.asyncio
async def test_request_limit_is_enforced() -> None:
    async def fake_sender(request: ReportRequest) -> ReportResult:
        return ReportResult(TestStatus.SUCCESS, request.target_id, request.report_type)

    service = ReportTestService(fake_sender)
    requests = [
        ReportRequest(f"test-{index}", ReportType.OTHER)
        for index in range(11)
    ]

    with pytest.raises(ValueError):
        await service.run_test("limit", requests)
