"""Gemini adapter behind the LLM provider interface.

Targets the Gemini Interactions API
(``POST /v1beta/interactions``) with a JSON ``response_format`` schema for strict
structured output. Networking is injectable so tests never call the network. The
API key is sent as a header (never in the URL) and never logged; only the public
excerpts and stable graph text assembled by the prompt builders are transmitted.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from typing import Any

from app.services.reasoning.provider import LlmError, LlmRequest

Transport = Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]]


def inline_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve local ``$defs`` references into a self-contained schema.

    Pydantic emits enums and nested models under ``$defs`` with ``$ref`` links.
    The Interactions API accepts a subset of JSON Schema, so we inline those
    definitions and drop ``$defs`` to avoid relying on unsupported references.
    """
    defs = schema.get("$defs", {})
    # Keys pydantic emits that the structured-output subset does not need and may
    # reject. Dropping them keeps the schema inside the accepted subset.
    dropped = {"$defs", "title", "additionalProperties"}

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/$defs/"):
                target = defs.get(ref.split("/")[-1], {})
                return resolve(dict(target))
            return {key: resolve(value) for key, value in node.items() if key not in dropped}
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    resolved = resolve(schema)
    assert isinstance(resolved, dict)
    return resolved


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
        # The Interactions API has no separate system field for structured output;
        # the verbatim system contract is prepended so it always reaches the model.
        prompt = f"{request.system}\n\n{request.user}"
        # Defensive data-boundary check: never let the key leak into prompt text.
        if self._api_key in prompt:
            raise LlmError("refusing to send a request that contains the API key")
        body: dict[str, Any] = {
            "model": self.model,
            "input": prompt,
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": inline_json_schema(request.json_schema),
            },
        }
        url = f"{self.base_url}/v1beta/interactions"
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
    """Pull the JSON text out of an Interactions response, defensively.

    The output lives at ``steps[].content[].text`` for the ``model_output`` step.
    """
    if payload.get("status") == "failed":
        raise LlmError("Gemini interaction reported status=failed")
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise LlmError("Gemini response contained no steps")

    model_steps = [
        step for step in steps if isinstance(step, dict) and step.get("type") == "model_output"
    ]
    for step in model_steps or [s for s in steps if isinstance(s, dict)]:
        content = step.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str) and text.strip():
                    return text
    raise LlmError("Gemini response contained no model_output text")
