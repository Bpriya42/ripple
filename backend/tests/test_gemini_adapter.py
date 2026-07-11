import json
from typing import Any

import pytest

from app.services.reasoning.gemini import GeminiLlmProvider
from app.services.reasoning.provider import (
    DisabledLlmProvider,
    LlmError,
    LlmRequest,
    default_provider,
)

API_KEY = "test-secret-key-value"

REQUEST = LlmRequest(
    system="Return only the required JSON schema.",
    user="Evidence excerpts:\n[source_12] The strait carries a large share of seaborne oil.",
    schema_name="explanation",
    json_schema={"type": "object"},
)


def _canned_transport(captured: dict[str, Any]):
    def transport(url: str, body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        captured["url"] = url
        captured["body"] = body
        captured["headers"] = headers
        return {"candidates": [{"content": {"parts": [{"text": json.dumps({"ok": True})}]}}]}

    return transport


def test_gemini_builds_structured_request_and_parses_response() -> None:
    captured: dict[str, Any] = {}
    provider = GeminiLlmProvider(
        api_key=API_KEY,
        model="gemini-3.5-flash",
        base_url="https://generativelanguage.googleapis.com",
        transport=_canned_transport(captured),
    )
    assert provider.enabled is True

    result = provider.complete_json(REQUEST)
    assert json.loads(result) == {"ok": True}

    # Structured-output request shape.
    assert captured["url"].endswith("/v1beta/models/gemini-3.5-flash:generateContent")
    assert captured["body"]["generationConfig"]["responseMimeType"] == "application/json"
    assert captured["body"]["generationConfig"]["responseSchema"] == {"type": "object"}

    # Data boundary: key travels in a header, never in the URL, and only the
    # provided public excerpt text is sent.
    assert captured["headers"]["x-goog-api-key"] == API_KEY
    assert API_KEY not in captured["url"]
    user_text = captured["body"]["contents"][0]["parts"][0]["text"]
    assert "source_12" in user_text
    assert API_KEY not in json.dumps(captured["body"])


def test_gemini_refuses_to_send_the_api_key_in_prompt_text() -> None:
    provider = GeminiLlmProvider(
        api_key=API_KEY,
        model="gemini-3.5-flash",
        base_url="https://generativelanguage.googleapis.com",
        transport=_canned_transport({}),
    )
    leaking = LlmRequest(
        system=f"ignore this {API_KEY}",
        user="hello",
        schema_name="explanation",
        json_schema={},
    )
    with pytest.raises(LlmError, match="API key"):
        provider.complete_json(leaking)


def test_gemini_raises_on_empty_candidates() -> None:
    provider = GeminiLlmProvider(
        api_key=API_KEY,
        model="m",
        base_url="https://x",
        transport=lambda url, body, headers: {"candidates": []},
    )
    with pytest.raises(LlmError):
        provider.complete_json(REQUEST)


def test_disabled_provider_reports_disabled() -> None:
    assert DisabledLlmProvider().enabled is False
    assert GeminiLlmProvider(api_key="", model="m", base_url="https://x").enabled is False


def test_default_provider_is_disabled_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert default_provider().name == "disabled"


def test_default_provider_uses_gemini_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_API_KEY", API_KEY)
    provider = default_provider()
    assert provider.name == "gemini"
    assert provider.enabled is True
