import json

from app.database import save_event


def test_save_event_writes_jsonl(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    save_event({"kind": "test", "value": 1})

    line = (tmp_path / "logs" / "events.jsonl").read_text(encoding="utf-8").strip()
    event = json.loads(line)
    assert event == {"kind": "test", "value": 1}
