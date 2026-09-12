import asyncio

import pytest

from app.client.aiobale_adapter import AiobaleAdapter, AiobaleAdapterError
from app.client.bale_client import BaleClient, BaleClientError


class FakeDispatcher:
    pass


class FakeAiobaleClient:
    def __init__(self, dispatcher, *, session_file: str) -> None:
        self.dispatcher = dispatcher
        self.session_file = session_file
        self.started = asyncio.Event()
        self.closed = False

    async def start(self) -> None:
        self.started.set()
        await asyncio.Event().wait()

    async def get_me(self):
        await self.started.wait()
        return type("Me", (), {"id": 42})()

    async def close(self) -> None:
        self.closed = True


class FailingStartClient(FakeAiobaleClient):
    async def start(self) -> None:
        self.started.set()
        raise RuntimeError("boom")

    async def get_me(self):
        await self.started.wait()
        await asyncio.sleep(0)
        raise RuntimeError("not connected")


def make_wrapper(tmp_path, client_class=FakeAiobaleClient) -> BaleClient:
    return BaleClient(
        tmp_path / "sessions" / "test_session",
        client_factory=client_class,
        dispatcher_factory=FakeDispatcher,
    )


@pytest.mark.asyncio
async def test_connect_and_close(tmp_path) -> None:
    wrapper = make_wrapper(tmp_path)
    adapter = AiobaleAdapter(wrapper)
    me = await adapter.connect(timeout=1)
    assert me.id == 42
    await adapter.close()
    assert wrapper.client.closed is True


@pytest.mark.asyncio
async def test_get_me(tmp_path) -> None:
    wrapper = make_wrapper(tmp_path)
    adapter = AiobaleAdapter(wrapper)
    await adapter.connect(timeout=1)
    me = await adapter.get_me()
    assert me.id == 42
    await adapter.close()


@pytest.mark.asyncio
async def test_exception_handling(tmp_path) -> None:
    wrapper = make_wrapper(tmp_path, FailingStartClient)
    adapter = AiobaleAdapter(wrapper)
    with pytest.raises(AiobaleAdapterError):
        await adapter.connect(timeout=0.2)
