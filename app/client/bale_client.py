from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any


class BaleClientError(RuntimeError):
    """Normalized error raised by the low-level aiobale wrapper."""


class BaleClient:
    """
    Thin lifecycle wrapper around aiobale-py.

    The verified aiobale-py 0.3.8 public API constructs a Client with a
    Dispatcher and ``session_file=...`` and starts it with ``await client.start()``.
    Authentication remains fully delegated to aiobale, so OTP values never pass
    through this project and cannot be logged here.
    """

    def __init__(
        self,
        session_file: str | Path,
        *,
        client_factory: Callable[..., Any] | None = None,
        dispatcher_factory: Callable[[], Any] | None = None,
    ) -> None:
        if client_factory is None or dispatcher_factory is None:
            try:
                from aiobale import Client, Dispatcher
            except ImportError as exc:  # pragma: no cover - environment dependent
                raise BaleClientError(
                    "aiobale-py is not installed. Run: python -m pip install -r requirements.txt"
                ) from exc
            client_factory = client_factory or Client
            dispatcher_factory = dispatcher_factory or Dispatcher

        self.dispatcher = dispatcher_factory()
        self.session_file = Path(session_file)
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.client = client_factory(
            self.dispatcher,
            session_file=str(self.session_file),
        )
        self._start_task: asyncio.Task[Any] | None = None

    async def start_forever(self) -> None:
        """Start aiobale normally; intended for the main bot process."""
        try:
            await self.client.start()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise BaleClientError(f"Bale client failed: {exc}") from exc

    async def connect(self, *, timeout: float = 20.0, probe_interval: float = 0.25) -> Any:
        """
        Start the client in a task and verify authenticated connectivity via get_me().

        This is used by --check-connection so it can verify connectivity without
        intentionally sending any report action or remaining in the update loop.
        """
        if self._start_task is not None and not self._start_task.done():
            return await self.get_me()

        self._start_task = asyncio.create_task(self.client.start(), name="aiobale-start")
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        last_error: Exception | None = None

        while loop.time() < deadline:
            if self._start_task.done():
                task_exc = self._start_task.exception()
                if task_exc is not None:
                    raise BaleClientError(f"Bale client failed to start: {task_exc}") from task_exc
            try:
                return await asyncio.wait_for(self.get_me(), timeout=min(2.0, timeout))
            except (BaleClientError, TimeoutError) as exc:
                last_error = exc
                if self._start_task.done():
                    task_exc = self._start_task.exception()
                    if task_exc is not None:
                        raise BaleClientError(
                            f"Bale client failed to start: {task_exc}"
                        ) from task_exc
                await asyncio.sleep(probe_interval)

        if self._start_task.done():
            task_exc = self._start_task.exception()
            if task_exc is not None:
                raise BaleClientError(f"Bale client failed to start: {task_exc}") from task_exc
        else:
            self._start_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._start_task

        raise BaleClientError(
            f"connection verification timed out after {timeout:.1f}s"
            + (f"; last error: {last_error}" if last_error else "")
        )

    async def get_me(self) -> Any:
        get_me = getattr(self.client, "get_me", None)
        if get_me is None or not callable(get_me):
            raise BaleClientError("installed aiobale Client does not expose get_me()")
        try:
            return await get_me()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise BaleClientError(f"get_me failed: {exc}") from exc

    async def close(self) -> None:
        """Cancel the running start task and call a supported shutdown hook if exposed."""
        if self._start_task is not None:
            if not self._start_task.done():
                self._start_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._start_task
            else:
                # Retrieve any exception so asyncio does not emit an unhandled-task warning.
                with suppress(asyncio.CancelledError):
                    self._start_task.exception()

        # Shutdown method names are resolved from the installed object instead of
        # assuming an undocumented method. This keeps the wrapper compatible while
        # the public 0.3.8 README only documents construction/start semantics.
        for method_name in ("close", "stop", "disconnect"):
            method = getattr(self.client, method_name, None)
            if method is None or not callable(method):
                continue
            try:
                result = method()
                if asyncio.iscoroutine(result):
                    await result
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise BaleClientError(f"Bale client shutdown failed: {exc}") from exc
            break
