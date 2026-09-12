from __future__ import annotations

from typing import Any

from app.config import Settings
from app.reports.models import ReportRequest, ReportType
from app.reports.service import ReportTestService, ReportServiceError


async def handle_start(message: Any) -> None:
    await message.reply(
        "Bale Security Test Harness is active. "
        "Report tests are mock-only and bounded by local safety settings."
    )


async def handle_status(message: Any, settings: Settings) -> None:
    mode = "ENABLED" if settings.test_mode else "DISABLED"
    await message.reply(
        f"Test mode: {mode}\n"
        f"Max requests/test: {settings.max_test_requests}\n"
        f"Request delay: {settings.request_delay:.2f}s\n"
        "Real Bale report sending: NOT IMPLEMENTED"
    )


async def handle_test(message: Any, service: ReportTestService) -> None:
    request = ReportRequest(
        target_id="TEST_TARGET",
        report_type=ReportType.OTHER,
        description="controlled mock handler test",
    )
    try:
        result = await service.run_test("handler_mock_test", [request])
    except ReportServiceError as exc:
        await message.reply(f"Mock test blocked: {exc}")
        return

    item = result.results[0]
    await message.reply(
        f"Mock test completed: {item.status.value}\n"
        f"Duration: {item.duration or 0.0:.4f}s\n"
        "No real report action was executed."
    )


async def handle_help(message: Any) -> None:
    await message.reply(
        "/start - harness information\n"
        "/status - local safety configuration\n"
        "/test - run exactly one mock report scenario\n"
        "/help - show this help\n\n"
        "This project has no command for real or bulk reporting."
    )


def register_handlers(dispatcher: Any, settings: Settings, service: ReportTestService) -> None:
    """Register aiobale handlers using the public F.text filtering API."""
    try:
        from aiobale import F
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("aiobale-py is required to register Bale handlers") from exc

    @dispatcher.message(F.text == "/start")
    async def _start(message: Any) -> None:
        await handle_start(message)

    @dispatcher.message(F.text == "/status")
    async def _status(message: Any) -> None:
        await handle_status(message, settings)

    @dispatcher.message(F.text == "/test")
    async def _test(message: Any) -> None:
        await handle_test(message, service)

    @dispatcher.message(F.text == "/help")
    async def _help(message: Any) -> None:
        await handle_help(message)
