from __future__ import annotations

import argparse
import asyncio

from app.client.bale_client import BaleClient
from app.config import settings, validate_config
from app.database import save_event


async def check_connection() -> None:
    """Connect using the configured test session and close cleanly."""
    client = BaleClient(settings.session_name)

    try:
        print(f"Connecting with session: {settings.session_name}")
        await client.connect()
        print("Aiobale connection established.")
        save_event(
            {
                "event": "connection_check",
                "status": "success",
                "session": settings.session_name,
            }
        )
    except Exception as exc:
        save_event(
            {
                "event": "connection_check",
                "status": "failed",
                "session": settings.session_name,
                "error": str(exc),
            }
        )
        raise
    finally:
        await client.close()
        print("Connection closed cleanly.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Controlled Bale/Aiobale security-test harness"
    )
    parser.add_argument(
        "--check-connection",
        action="store_true",
        help="connect with the configured test session and close it safely",
    )
    args = parser.parse_args()

    validate_config()

    if args.check_connection:
        asyncio.run(check_connection())
        return

    print("Bale security test harness is configured.")
    print("TEST_MODE is enabled.")
    print("No report action is performed by default.")
    print("Run with --check-connection to validate the Aiobale connection.")


if __name__ == "__main__":
    main()
