from app.reports.models import (
    ReportRequest,
    ReportResult,
    ReportType,
    SecurityTestResult,
    TestStatus as Status,
)


def test_enum_values() -> None:
    assert ReportType.SPAM.value == "spam"
    assert Status.RATE_LIMITED.value == "rate_limited"


def test_report_request_and_result() -> None:
    request = ReportRequest(" TEST_TARGET ", ReportType.OTHER)
    result = ReportResult(Status.SUCCESS, request.target_id, request.report_type)
    assert request.target_id == "TEST_TARGET"
    assert result.status is Status.SUCCESS


def test_success_rate() -> None:
    summary = SecurityTestResult("demo")
    summary.add_result(ReportResult(Status.SUCCESS, "T", ReportType.OTHER))
    summary.add_result(ReportResult(Status.FAILED, "T", ReportType.OTHER))
    assert summary.success_rate == 50.0


def test_empty_success_rate_is_zero() -> None:
    assert SecurityTestResult("empty").success_rate == 0.0
