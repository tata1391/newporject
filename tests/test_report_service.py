import pytest

from app.reports.models import ReportRequest, ReportResult, ReportType, TestStatus
from app.reports.service import ReportTestService


@pytest.mark.asyncio
async def test_run_test_with_fake_sender(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_sender(request: ReportRequest) -> ReportResult:
        return ReportResult(
            status=TestStatus.SUCCESS,
            target_id=request.target_id,
            report_type=request.report_type,
            message="simulated",
        )

    monkeypatch.setattr("app.reports.service.settings.request_delay", 0.0)
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
async def test_sender_exception_becomes_failed_result(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_sender(request: ReportRequest) -> ReportResult:
        raise RuntimeError("simulated failure")

    monkeypatch.setattr("app.reports.service.settings.request_delay", 0.0)
    service = ReportTestService(failing_sender)
    result = await service.run_test(
        "failure",
        [ReportRequest("test-1", ReportType.OTHER)],
    )

    assert result.failed == 1
    assert result.results[0].status == TestStatus.FAILED
    assert "simulated failure" in result.results[0].message


@pytest.mark.asyncio
async def test_request_limit_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.reports.service.settings.max_test_requests", 1)
    monkeypatch.setattr("app.reports.service.settings.request_delay", 0.0)

    async def fake_sender(request: ReportRequest) -> ReportResult:
        return ReportResult(TestStatus.SUCCESS, request.target_id, request.report_type)

    service = ReportTestService(fake_sender)

    with pytest.raises(ValueError):
        await service.run_test(
            "limit",
            [
                ReportRequest("test-1", ReportType.OTHER),
                ReportRequest("test-2", ReportType.OTHER),
            ],
        )
