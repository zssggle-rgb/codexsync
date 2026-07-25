"""Tests for config.toml parsing logic."""

from codexsync.config import read_profiles, available_providers


def test_read_profiles_returns_dict():
    """read_profiles should always return a dict (possibly empty)."""
    result = read_profiles()
    assert isinstance(result, dict)


def test_available_providers_includes_builtins():
    """available_providers must include built-in openai and deepseek."""
    providers = available_providers()
    assert "openai" in providers
    assert "deepseek" in providers
    assert "model" in providers["openai"]
    assert "model_provider" in providers["openai"]
