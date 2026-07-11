import json
from typing import Any

import pytest

from app.services.reasoning.gemini import GeminiLlmProvider, inline_json_schema
from app.services.reasoning.provider import (
    DisabledLlmProvider,
    LlmError,
    LlmRequest,
    default_provider,
)
from app.services.reasoning.schemas import Explanation

API_KEY = "test-secret-key-value"

REQUEST = LlmRequest(
    system="Return only the required JSON schema.",
    user="Evidence excerpts:\n[source_12] The strait carries a large share of seaborne oil.",
    schema_name="explanation",
    json_schema={"type": "object"},
)


def _interaction(text: str) -> dict[str, Any]:
    return {
        "id": "v1_test",
        "model": "gemini-3.5-flash",
        "status": "completed",
        "steps": [{"type": "model_output", "content": [{"type": "text", "text": text}]}],
    }


def _canned_transport(captured: dict[str, Any]):
    def transport(url: str, body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        captured["url"] = url
        captured["body"] = body
        captured["headers"] = headers
        return _interaction(json.dumps({"ok": True}))

    return transport


def test_gemini_builds_interactions_request_and_parses_response() -> None:
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

    # Interactions API request shape.
    assert captured["url"] == "https://generativelanguage.googleapis.com/v1beta/interactions"
    assert captured["body"]["model"] == "gemini-3.5-flash"
    assert captured["body"]["response_format"]["mime_type"] == "application/json"
    assert captured["body"]["response_format"]["type"] == "text"
    # The verbatim system contract is delivered inside the input.
    assert "Return only the required JSON schema." in captured["body"]["input"]
    assert "source_12" in captured["body"]["input"]

    # Data boundary: key travels in a header, never in the URL or the body.
    assert captured["headers"]["x-goog-api-key"] == API_KEY
    assert API_KEY not in captured["url"]
    assert API_KEY not in json.dumps(captured["body"])


def test_inline_json_schema_resolves_enum_defs() -> None:
    schema = Explanation.model_json_schema()
    inlined = inline_json_schema(schema)
    assert "$defs" not in inlined
    # The ClaimState enum is inlined as a concrete list of allowed values.
    claim_state = inlined["properties"]["claim_state"]
    assert "conditional_pathway" in claim_state.get("enum", [])
    assert "$ref" not in json.dumps(inlined)


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


def test_gemini_raises_on_empty_steps() -> None:
    provider = GeminiLlmProvider(
        api_key=API_KEY,
        model="m",
        base_url="https://x",
        transport=lambda url, body, headers: {"status": "completed", "steps": []},
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
