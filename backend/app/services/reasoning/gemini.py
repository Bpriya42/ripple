"""Gemini adapter behind the LLM provider interface.

Uses the Generative Language ``generateContent`` endpoint with a JSON
``responseSchema`` for strict structured output. Networking is injectable so
tests never call the network. The API key is sent as a header (never in the URL)
and never logged; only the public excerpts and stable graph text assembled by the
prompt builders are transmitted.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from typing import Any

from app.services.reasoning.provider import LlmError, LlmRequest

Transport = Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]]


class GeminiLlmProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        *,
        transport: Transport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport or self._http_transport

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    def complete_json(self, request: LlmRequest) -> str:
        # Defensive data-boundary check: never let the key leak into prompt text.
        if self._api_key in request.system or self._api_key in request.user:
            raise LlmError("refusing to send a request that contains the API key")
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": request.system}]},
            "contents": [{"role": "user", "parts": [{"text": request.user}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": request.json_schema,
                "temperature": 0,
            },
        }
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self._api_key}
        payload = self._transport(url, body, headers)
        return _extract_text(payload)

    def _http_transport(
        self, url: str, body: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        request = urllib.request.Request(  # noqa: S310 - fixed https Google endpoint
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
            raw = response.read().decode("utf-8", "replace")
        parsed: Any = json.loads(raw)
        if not isinstance(parsed, dict):
            raise LlmError("unexpected Gemini response shape")
        return parsed


def _extract_text(payload: dict[str, Any]) -> str:
    """Pull the JSON text out of a generateContent response, defensively."""
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise LlmError("Gemini response contained no candidates")
    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list) or not parts:
        raise LlmError("Gemini response contained no content parts")
    text = parts[0].get("text") if isinstance(parts[0], dict) else None
    if not isinstance(text, str) or not text.strip():
        raise LlmError("Gemini response contained no text")
    return text
