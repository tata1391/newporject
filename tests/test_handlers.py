from dataclasses import replace

import pytest

from app.config import Settings
from app.handlers.bot_handlers import handle_help, handle_start, handle_status, handle_test
from app.reports.service import ReportTestService
from tests.mocks import MockReportSender


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply(self, text: str) -> None:
        self.replies.append(text)


@pytest.mark.asyncio
async def test_start_handler() -> None:
    message = FakeMessage()
    await handle_start(message)
    assert "mock-only" in message.replies[0]


@pytest.mark.asyncio
async def test_status_handler() -> None:
    message = FakeMessage()
    settings = replace(Settings(), max_test_requests=3, request_delay=0.25)
    await handle_status(message, settings)
    assert "Max requests/test: 3" in message.replies[0]
    assert "NOT IMPLEMENTED" in message.replies[0]


@pytest.mark.asyncio
async def test_test_handler_executes_one_mock() -> None:
    message = FakeMessage()
    sender = MockReportSender()
    service = ReportTestService(sender, request_delay=0)
    await handle_test(message, service)
    assert sender.calls == 1
    assert "No real report action" in message.replies[0]


@pytest.mark.asyncio
async def test_help_handler() -> None:
    message = FakeMessage()
    await handle_help(message)
    assert "/test" in message.replies[0]
    assert "no command for real or bulk reporting" in message.replies[0]
