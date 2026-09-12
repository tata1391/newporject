from __future__ import annotations

from typing import Any

from app.client.bale_client import BaleClient, BaleClientError


class AiobaleAdapterError(RuntimeError):
    """Stable application-level exception for aiobale lifecycle failures."""


class AiobaleAdapter:
    def __init__(self, client: BaleClient) -> None:
        self._client = client

    @property
    def dispatcher(self) -> Any:
        return self._client.dispatcher

    async def connect(self, *, timeout: float = 20.0) -> Any:
        try:
            return await self._client.connect(timeout=timeout)
        except BaleClientError as exc:
            raise AiobaleAdapterError(str(exc)) from exc

    async def close(self) -> None:
        try:
            await self._client.close()
        except BaleClientError as exc:
            raise AiobaleAdapterError(str(exc)) from exc

    async def get_me(self) -> Any:
        try:
            return await self._client.get_me()
        except BaleClientError as exc:
            raise AiobaleAdapterError(str(exc)) from exc

    async def start_forever(self) -> None:
        try:
            await self._client.start_forever()
        except BaleClientError as exc:
            raise AiobaleAdapterError(str(exc)) from exc
