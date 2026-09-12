from pathlib import Path

import pytest

from app.config import ConfigError, Settings


def test_valid_settings() -> None:
    settings = Settings(request_delay=0, max_test_requests=1).validate()
    assert settings.test_mode is True


def test_negative_delay_rejected() -> None:
    with pytest.raises(ConfigError):
        Settings(request_delay=-0.1).validate()


def test_invalid_session_path_rejected() -> None:
    with pytest.raises(ConfigError):
        Settings(bale_session_name="../secret").validate()


def test_session_stays_in_sessions_dir() -> None:
    settings = Settings(bale_session_name="abc")
    assert settings.session_file == Path("sessions") / "abc"
