from __future__ import annotations

from typing import Any


class AiobaleUnavailable(RuntimeError):
    """Raised when the Aiobale dependency is not installed."""


class AiobaleAdapter:
    """Small, version-conscious adapter around Aiobale.

    This layer only establishes a client/dispatcher boundary. It deliberately
    does not implement report submission or bulk actions.
    """

    def __init__(self, session_name: str) -> None:
        self.session_name = session_name
        self.client: Any | None = None
        self.dispatcher: Any | None = None

    def build(self) -> Any:
        try:
            from aiobale import Client, Dispatcher
        except ImportError as exc:
            raise AiobaleUnavailable(
                "Aiobale نصب نیست. ابتدا dependency پروژه را نصب کن."
            ) from exc

        self.dispatcher = Dispatcher()

        # Current Aiobale examples use Client(dispatcher=...).
        # Keep construction isolated here so API changes only affect this file.
        self.client = Client(dispatcher=self.dispatcher)
        return self.client

    async def connect(self) -> None:
        if self.client is None:
            self.build()

        connect = getattr(self.client, "connect", None)
        if connect is None:
            raise RuntimeError(
                "نسخه نصب‌شده Aiobale متد connect() ندارد؛ API نسخه را بررسی کن."
            )

        result = connect()
        if hasattr(result, "__await__"):
            await result

    async def close(self) -> None:
        if self.client is None:
            return

        close = getattr(self.client, "close", None)
        if close is None:
            return

        result = close()
        if hasattr(result, "__await__"):
            await result
