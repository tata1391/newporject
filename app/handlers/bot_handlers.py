from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HandlerResponse:
    """Safe response returned by command handlers."""

    text: str


def help_response() -> HandlerResponse:
    """Return the available local test commands."""
    return HandlerResponse(
        text=(
            "Security test harness\n"
            "/status - show local test status\n"
            "/help - show this help\n"
            "Real-world mass reporting is disabled."
        )
    )


def status_response(test_mode: bool) -> HandlerResponse:
    """Return a concise status message."""
    state = "enabled" if test_mode else "disabled"
    return HandlerResponse(text=f"TEST_MODE: {state}")
