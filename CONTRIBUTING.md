# Contributing

## Development

1. Keep tests isolated from real-world report targets.
2. Do not add code that bypasses platform anti-abuse controls or sends bulk reports.
3. Add or update tests for behavioral changes.
4. Run `pytest` and `ruff check .` before submitting changes.

## Pull requests

Describe the test scenario, expected behavior, and any safety assumptions. Never include tokens, session files, or other secrets in commits.
