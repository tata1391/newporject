from app.reports.models import (
    ReportRequest,
    ReportType,
    SecurityTestResult,
    TestStatus,
)


def test_report_request_defaults_description() -> None:
    request = ReportRequest("test-target", ReportType.OTHER)
    assert request.description == ""


def test_success_rate_is_zero_without_requests() -> None:
    result = SecurityTestResult(test_name="empty")
    assert result.success_rate == 0.0


def test_success_rate_is_calculated() -> None:
    result = SecurityTestResult(test_name="sample", total_requests=4, successful=3)
    assert result.success_rate == 75.0


def test_enum_values_are_stable() -> None:
    assert ReportType.SPAM.value == "spam"
    assert TestStatus.RATE_LIMITED.value == "rate_limited"
