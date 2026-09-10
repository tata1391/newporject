from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BaleClient:
    """Thin adapter for the Bale client used by the test harness.

    The concrete aiobale integration is intentionally injected instead of
    guessing version-specific APIs.
    """

    client: Any | None = None

    async def connect(self) -> None:
        if self.client is None:
            return
        connect = getattr(self.client, "connect", None)
        if connect is not None:
            result = connect()
            if hasattr(result, "__await__"):
                await result

    async def close(self) -> None:
        if self.client is None:
            return
        close = getattr(self.client, "close", None)
        if close is not None:
            result = close()
            if hasattr(result, "__await__"):
                await result
