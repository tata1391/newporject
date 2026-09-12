from __future__ import annotations

import inspect
from typing import Any


class AiobaleUnavailable(RuntimeError):
    """Raised when the Aiobale dependency is not installed."""


class AiobaleConnectionError(RuntimeError):
    """Raised when the Aiobale client cannot be connected safely."""


class AiobaleAdapter:
    """Version-aware connection adapter for Enalite/aiobale.

    This layer is intentionally limited to dependency loading, client
    construction, authentication/connection startup, and clean shutdown.
    It does not expose report submission, bulk actions, or anti-abuse bypasses.
    """

    def __init__(self, session_name: str) -> None:
        self.session_name = session_name
        self.client: Any | None = None
        self.dispatcher: Any | None = None

    @staticmethod
    def _awaitable(value: Any) -> bool:
        return inspect.isawaitable(value)

    def build(self) -> Any:
        try:
            from aiobale import Client, Dispatcher
        except ImportError as exc:
            raise AiobaleUnavailable(
                "Aiobale نصب نیست. requirements.txt را نصب کن."
            ) from exc

        self.dispatcher = Dispatcher()

        # Aiobale currently documents Client(dispatcher=...). Some versions
        # also accept a session_file/session_name argument. We inspect the
        # constructor rather than hard-coding a version-specific keyword.
        try:
            signature = inspect.signature(Client)
            parameters = signature.parameters
        except (TypeError, ValueError):
            parameters = {}

        kwargs: dict[str, Any] = {}
        if "dispatcher" in parameters:
            kwargs["dispatcher"] = self.dispatcher

        if "session_file" in parameters:
            kwargs["session_file"] = self.session_name
        elif "session_name" in parameters:
            kwargs["session_name"] = self.session_name

        try:
            if kwargs:
                self.client = Client(**kwargs)
            else:
                self.client = Client(self.dispatcher)
        except TypeError as exc:
            raise AiobaleConnectionError(
                "ساخت Client با API نسخه نصب‌شده Aiobale انجام نشد. "
                "نسخه نصب‌شده را بررسی کن."
            ) from exc

        return self.client

    async def connect(self) -> Any:
        if self.client is None:
            self.build()

        assert self.client is not None

        # Newer Aiobale examples expose start(); older variants may expose
        # connect(). Prefer start() because it owns the authentication/session
        # lifecycle in the current Enalite release.
        start = getattr(self.client, "start", None)
        if callable(start):
            result = start()
            if self._awaitable(result):
                return await result
            return result

        connect = getattr(self.client, "connect", None)
        if callable(connect):
            result = connect()
            if self._awaitable(result):
                return await result
            return result

        raise AiobaleConnectionError(
            "نسخه نصب‌شده Aiobale متد start() یا connect() ندارد."
        )

    async def close(self) -> None:
        if self.client is None:
            return

        # Different releases use close()/stop(). Use the first available
        # lifecycle method and never invent a transport-level shutdown call.
        for method_name in ("close", "stop"):
            method = getattr(self.client, method_name, None)
            if not callable(method):
                continue

            result = method()
            if self._awaitable(result):
                await result
            return

    async def __aenter__(self) -> "AiobaleAdapter":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()
