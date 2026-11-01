import pytest
from agents import OpenAIChatCompletionsModel

from campus_mcp.agent import configure_model


def test_openai_provider(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-value-not-a-real-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    model, client = configure_model()
    assert model == "gpt-4.1-mini" and client is None


@pytest.mark.parametrize(
    "provider,key", [("openai", "OPENAI_API_KEY"), ("gemini", "GEMINI_API_KEY")]
)
def test_missing_key_has_actionable_error(monkeypatch, provider, key):
    monkeypatch.setenv("MODEL_PROVIDER", provider)
    monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError, match=key):
        configure_model()


async def test_gemini_uses_agents_sdk_model_adapter(monkeypatch):
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-value-not-a-real-key")
    model, client = configure_model()
    try:
        assert isinstance(model, OpenAIChatCompletionsModel)
        assert model.model == "gemini-3.1-flash-lite"
        assert str(client.base_url) == "https://generativelanguage.googleapis.com/v1beta/openai/"
    finally:
        await client.close()


def test_invalid_provider(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "unsupported")
    with pytest.raises(ValueError, match="MODEL_PROVIDER"):
        configure_model()
