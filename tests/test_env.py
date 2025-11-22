from earnings_call.env import get_int_env


def test_get_int_env_returns_default_for_blank(monkeypatch):
    monkeypatch.setenv("TEST_PORT", "")
    assert get_int_env("TEST_PORT", 1234) == 1234


def test_get_int_env_raises_for_bad_value(monkeypatch):
    monkeypatch.setenv("TEST_PORT", "abc")
    try:
        get_int_env("TEST_PORT", 1234)
    except ValueError as exc:
        assert "TEST_PORT" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ValueError when env value is not an integer")
