import sys
import types

import pytest

from app.client.aiobale_adapter import (
    AiobaleAdapter,
    AiobaleConnectionError,
    AiobaleUnavailable,
)


def test_adapter_requires_aiobale(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object):
        if name == "aiobale":
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    adapter = AiobaleAdapter("test-session")
    with pytest.raises(AiobaleUnavailable):
        adapter.build()


def test_adapter_builds_current_style_client_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeDispatcher:
        pass

    class FakeClient:
        def __init__(self, *, dispatcher, session_file):
            self.dispatcher = dispatcher
            self.session_file = session_file
            self.started = False
            self.closed = False

        async def start(self):
            self.started = True

        async def close(self):
            self.closed = True

    fake_module = types.ModuleType("aiobale")
    fake_module.Client = FakeClient
    fake_module.Dispatcher = FakeDispatcher
    monkeypatch.setitem(sys.modules, "aiobale", fake_module)

    adapter = AiobaleAdapter("test-session")
    client = adapter.build()

    assert client is adapter.client
    assert adapter.dispatcher is client.dispatcher
    assert client.session_file == "test-session"


@pytest.mark.asyncio
async def test_adapter_connect_and_close_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeDispatcher:
        pass

    class FakeClient:
        def __init__(self, *, dispatcher, session_file):
            self.dispatcher = dispatcher
            self.session_file = session_file
            self.started = False
            self.closed = False

        async def start(self):
            self.started = True

        async def close(self):
            self.closed = True

    fake_module = types.ModuleType("aiobale")
    fake_module.Client = FakeClient
    fake_module.Dispatcher = FakeDispatcher
    monkeypatch.setitem(sys.modules, "aiobale", fake_module)

    adapter = AiobaleAdapter("test-session")
    await adapter.connect()

    assert adapter.client is not None
    assert adapter.client.started is True

    await adapter.close()
    assert adapter.client.closed is True


@pytest.mark.asyncio
async def test_adapter_fails_clearly_without_lifecycle_method(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeDispatcher:
        pass

    class FakeClient:
        def __init__(self, *, dispatcher):
            self.dispatcher = dispatcher

    fake_module = types.ModuleType("aiobale")
    fake_module.Client = FakeClient
    fake_module.Dispatcher = FakeDispatcher
    monkeypatch.setitem(sys.modules, "aiobale", fake_module)

    adapter = AiobaleAdapter("test-session")
    with pytest.raises(AiobaleConnectionError):
        await adapter.connect()
