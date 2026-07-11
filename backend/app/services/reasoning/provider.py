"""LLM provider interface, offline implementations, and strict validation.

Per the build handoff, a provider interface with a disabled implementation
exists first; Gemini is added behind the same interface. Model output is always
validated against a strict schema, retried once on invalid output, and otherwise
raises so the caller can fall back to deterministic behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ValidationError

from app.core.config import llm_api_key, llm_base_url, llm_model, llm_provider


class LlmError(Exception):
    """Base class for enrichment provider failures."""


class LlmUnavailable(LlmError):
    """Raised when no live provider is configured (disabled or missing key)."""


class LlmInvalidOutput(LlmError):
    """Raised when model output fails schema validation after one retry."""


@dataclass(frozen=True)
class LlmRequest:
    system: str
    user: str
    schema_name: str
    json_schema: dict[str, object]


class LlmProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def enabled(self) -> bool: ...

    def complete_json(self, request: LlmRequest) -> str: ...


class DisabledLlmProvider:
    """Default provider: performs no model calls."""

    name = "disabled"
    enabled = False

    def complete_json(self, request: LlmRequest) -> str:
        raise LlmUnavailable("LLM provider is disabled; deterministic behavior only")


class ScriptedLlmProvider:
    """Offline provider that replays queued responses per schema (tests/eval)."""

    name = "scripted"
    enabled = True

    def __init__(self, responses: dict[str, list[str]]) -> None:
        self._responses = {name: list(values) for name, values in responses.items()}

    def complete_json(self, request: LlmRequest) -> str:
        queue = self._responses.get(request.schema_name)
        if not queue:
            raise LlmError(f"no scripted response queued for {request.schema_name}")
        return queue.pop(0)


def parse_with_retry[T: BaseModel](
    provider: LlmProvider, request: LlmRequest, schema: type[T]
) -> T:
    """Validate model output against ``schema``, retrying once on invalid output.

    ``LlmUnavailable`` from a disabled provider propagates immediately and is not
    retried. Only schema-invalid output is retried, exactly once.
    """
    last_error: ValidationError | None = None
    for _ in range(2):
        raw = provider.complete_json(request)
        try:
            return schema.model_validate_json(raw)
        except ValidationError as exc:
            last_error = exc
    raise LlmInvalidOutput(
        f"{request.schema_name} output failed validation after retry"
    ) from last_error


def default_provider() -> LlmProvider:
    """Build the configured provider, defaulting to disabled.

    Gemini is used only when ``LLM_PROVIDER=gemini`` and an API key is present;
    otherwise the disabled provider keeps the product fully deterministic.
    """
    if llm_provider() == "gemini":
        key = llm_api_key()
        if key:
            from app.services.reasoning.gemini import GeminiLlmProvider

            return GeminiLlmProvider(api_key=key, model=llm_model(), base_url=llm_base_url())
    return DisabledLlmProvider()
