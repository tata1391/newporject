import pytest

from app.client.aiobale_adapter import AiobaleAdapter, AiobaleUnavailable


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


def test_adapter_starts_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDispatcher:
        pass

    class FakeClient:
        def __init__(self, dispatcher):
            self.dispatcher = dispatcher

    class FakeAiobale:
        Client = FakeClient
        Dispatcher = FakeDispatcher

    monkeypatch.setitem(__import__("sys").modules, "aiobale", FakeAiobale())

    adapter = AiobaleAdapter("test-session")
    client = adapter.build()

    assert client is adapter.client
    assert adapter.dispatcher is client.dispatcher
