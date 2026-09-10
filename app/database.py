from __future__ import annotations

import json
from pathlib import Path
from typing import Any


LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def save_event(event: dict[str, Any], filename: str = "events.jsonl") -> None:
    """Append one structured test event to a local JSONL log."""
    path = LOG_DIR / filename
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
