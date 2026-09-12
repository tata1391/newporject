from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when project configuration is invalid."""


def _parse_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be true/false, got: {value!r}")


def _safe_session_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise ConfigError("BALE_SESSION_NAME cannot be empty")
    if Path(name).name != name or name in {".", ".."}:
        raise ConfigError("BALE_SESSION_NAME must be a plain file name, not a path")
    return name


@dataclass(frozen=True, slots=True)
class Settings:
    bale_session_name: str = "security_test_session"
    test_mode: bool = True
    max_test_requests: int = 10
    request_delay: float = 1.0
    session_dir: Path = Path("sessions")
    log_file: Path = Path("logs/events.jsonl")
    connection_timeout: float = 20.0

    def validate(self) -> "Settings":
        _safe_session_name(self.bale_session_name)
        if self.max_test_requests < 1:
            raise ConfigError("MAX_TEST_REQUESTS must be >= 1")
        if self.max_test_requests > 100:
            raise ConfigError("MAX_TEST_REQUESTS cannot exceed the hard safety cap of 100")
        if self.request_delay < 0:
            raise ConfigError("REQUEST_DELAY cannot be negative")
        if self.connection_timeout <= 0:
            raise ConfigError("CONNECTION_TIMEOUT must be > 0")
        return self

    @property
    def session_file(self) -> Path:
        # aiobale-py appends its own .bale suffix when needed; pass the stem/path.
        return self.session_dir / self.bale_session_name

    def ensure_directories(self) -> None:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


def load_settings(env_file: str | Path | None = ".env") -> Settings:
    if env_file is not None:
        load_dotenv(dotenv_path=env_file, override=False)

    try:
        max_requests = int(os.getenv("MAX_TEST_REQUESTS", "10"))
    except ValueError as exc:
        raise ConfigError("MAX_TEST_REQUESTS must be an integer") from exc

    try:
        request_delay = float(os.getenv("REQUEST_DELAY", "1.0"))
    except ValueError as exc:
        raise ConfigError("REQUEST_DELAY must be a number") from exc

    try:
        connection_timeout = float(os.getenv("CONNECTION_TIMEOUT", "20.0"))
    except ValueError as exc:
        raise ConfigError("CONNECTION_TIMEOUT must be a number") from exc

    settings = Settings(
        bale_session_name=_safe_session_name(
            os.getenv("BALE_SESSION_NAME", "security_test_session")
        ),
        test_mode=_parse_bool(os.getenv("TEST_MODE", "true"), name="TEST_MODE"),
        max_test_requests=max_requests,
        request_delay=request_delay,
        connection_timeout=connection_timeout,
    ).validate()
    settings.ensure_directories()
    return settings
