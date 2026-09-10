from app.handlers.bot_handlers import help_response, status_response


def test_help_response_mentions_safe_mode() -> None:
    response = help_response()
    assert "/help" in response.text
    assert "mass reporting" in response.text


def test_status_response() -> None:
    assert "enabled" in status_response(True).text
    assert "disabled" in status_response(False).text
