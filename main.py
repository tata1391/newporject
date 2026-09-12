from __future__ import annotations

import argparse
import asyncio
from typing import Any

from app.client.aiobale_adapter import AiobaleAdapter, AiobaleAdapterError
from app.client.bale_client import BaleClient
from app.config import ConfigError, Settings, load_settings
from app.database import JsonlEventLogger
from app.handlers.bot_handlers import register_handlers
from app.reports.service import ReportTestService, SenderResponse


async def _runtime_mock_sender(request: Any) -> SenderResponse:
    """Production entrypoint still uses a local mock: no network report action."""
    del request
    return SenderResponse(success=True, response_code=200, message="runtime mock success")


def _banner() -> None:
    print("================================")
    print(" Bale Security Test Harness")
    print("================================")
    print()


async def check_connection(settings: Settings) -> int:
    _banner()
    print("[1] Loading configuration...")
    print("[2] Loading session...")

    adapter = AiobaleAdapter(BaleClient(settings.session_file))
    try:
        print("[3] Connecting to Bale...")
        me = await adapter.connect(timeout=settings.connection_timeout)
        print("[4] Connection successful.")
        identity = getattr(me, "id", None) or getattr(me, "user_id", None)
        if identity is not None:
            print(f"    Authenticated identity: {identity}")
        print(f"[5] Test mode: {'ENABLED' if settings.test_mode else 'DISABLED'}")
        print("[6] No report action executed.")
        print("\nConnection check completed.")
        return 0
    except AiobaleAdapterError as exc:
        print(f"[ERROR] Connection check failed: {exc}")
        return 1
    finally:
        try:
            await adapter.close()
        except AiobaleAdapterError as exc:
            print(f"[WARN] Cleanup error: {exc}")


async def run_app(settings: Settings) -> int:
    event_logger = JsonlEventLogger(settings.log_file)
    service = ReportTestService(
        _runtime_mock_sender,
        test_mode=settings.test_mode,
        max_test_requests=settings.max_test_requests,
        request_delay=settings.request_delay,
        event_logger=event_logger,
    )

    adapter = AiobaleAdapter(BaleClient(settings.session_file))
    register_handlers(adapter.dispatcher, settings, service)

    _banner()
    print(f"Test mode: {'ENABLED' if settings.test_mode else 'DISABLED'}")
    print("Report sender: LOCAL MOCK ONLY")
    print("Starting Bale client. Press Ctrl+C to stop.")
    try:
        await adapter.start_forever()
        return 0
    except AiobaleAdapterError as exc:
        print(f"[ERROR] {exc}")
        return 1
    finally:
        try:
            await adapter.close()
        except AiobaleAdapterError as exc:
            print(f"[WARN] Cleanup error: {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bale Security Test Harness")
    parser.add_argument(
        "--check-connection",
        action="store_true",
        help="Authenticate/connect and exit without executing any report test",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2

    try:
        if args.check_connection:
            return asyncio.run(check_connection(settings))
        return asyncio.run(run_app(settings))
    except KeyboardInterrupt:
        print("\nStopped by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
