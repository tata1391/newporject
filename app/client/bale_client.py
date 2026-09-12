from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.client.aiobale_adapter import AiobaleAdapter


@dataclass
class BaleClient:
    """Application-level wrapper around the controlled Aiobale connection."""

    session_name: str
    adapter: AiobaleAdapter | None = None

    def __post_init__(self) -> None:
        if self.adapter is None:
            self.adapter = AiobaleAdapter(self.session_name)

    @property
    def client(self) -> Any | None:
        assert self.adapter is not None
        return self.adapter.client

    async def connect(self) -> Any:
        assert self.adapter is not None
        return await self.adapter.connect()

    async def close(self) -> None:
        assert self.adapter is not None
        await self.adapter.close()

    async def __aenter__(self) -> "BaleClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()
