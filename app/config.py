import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Kept for future authorized API adapters. The current Aiobale
    # connection uses its own session/authentication flow.
    bale_token: str = os.getenv("BALE_TOKEN", "")
    session_name: str = os.getenv("BALE_SESSION_NAME", "security_test_session")
    test_mode: bool = os.getenv("TEST_MODE", "true").lower() == "true"
    max_test_requests: int = int(os.getenv("MAX_TEST_REQUESTS", "10"))
    request_delay: float = float(os.getenv("REQUEST_DELAY", "1.0"))


settings = Settings()


def validate_config() -> None:
    if not settings.test_mode:
        raise RuntimeError(
            "TEST_MODE باید برای این پروژه روی true باشد."
        )

    if not settings.session_name.strip():
        raise ValueError(
            "BALE_SESSION_NAME نمی‌تواند خالی باشد."
        )

    if settings.max_test_requests < 1:
        raise ValueError(
            "MAX_TEST_REQUESTS باید حداقل 1 باشد."
        )

    if settings.request_delay < 0:
        raise ValueError(
            "REQUEST_DELAY نمی‌تواند منفی باشد."
        )
