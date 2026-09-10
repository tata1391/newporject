from app.config import validate_config


def main() -> None:
    validate_config()
    print("Bale security test harness is configured.")
    print("TEST_MODE is enabled; no real report action is performed by this entrypoint.")


if __name__ == "__main__":
    main()
