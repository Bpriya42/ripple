# Milestone 4 — Gemini enrichment

Milestone 4 adds an optional LLM enrichment layer that explains claims in plain
language. It is strictly additive: the deterministic publication policy remains
the sole authority on certainty and publication eligibility, and the default
provider is disabled, so Milestones 0–3 behave identically with no model calls.

## Delivered

- Provider interface with a **disabled default** (`DisabledLlmProvider`), an
  offline `ScriptedLlmProvider` for tests, and a `GeminiLlmProvider` behind the
  same interface. `default_provider()` returns Gemini only when
  `LLM_PROVIDER=gemini` and `LLM_API_KEY` are both set.
- The four verbatim prompt contracts (event-fact extraction, applicability,
  explanation, faithfulness review) with strict Pydantic/JSON schemas. Model
  output is validated, **retried once** on invalid output, and otherwise falls
  back deterministically.
- Enrichment orchestrator with deterministic-policy supremacy:
  - suppresses before any model call when the policy does not permit publication;
  - requires the model to **preserve the exact claim state** (an attempt to
    elevate a conditional pathway to an observed effect is rejected);
  - requires conditional language for conditional pathways;
  - rejects citations of unknown excerpts;
  - publishes prose only when the faithfulness review marks **every** sentence
    supported by cited excerpts; otherwise suppresses.
- Applicability over-claims are clamped to a safe state; the model can never
  report a met condition into publication.
- Gemini adapter uses the Generative Language `generateContent` endpoint with a
  JSON `responseSchema`, sends the key as a header (never the URL), refuses to
  transmit the key inside prompt text, and sends only the supplied public
  excerpts. Networking is injectable; tests never hit the network.
- An in-memory audit trace (provider, prompt version, steps, model claim state,
  faithfulness result) accompanies every result.
- `scripts/explain_claim.py` demonstrates the pipeline (`--demo` runs it fully
  offline with canned fixtures).

## Local acceptance gate

```powershell
uv run --project backend ruff format --check backend/app backend/alembic backend/tests scripts
uv run --project backend ruff check backend/app backend/alembic backend/tests scripts
uv run --project backend mypy backend/app scripts
uv run --project backend pytest -v
uv run --project backend python scripts/explain_claim.py --demo   # published, faithful, conditional
uv run --project backend python scripts/explain_claim.py          # disabled -> deterministic fallback
```

The eval suite (`backend/tests/test_enrichment.py`, `test_reasoning_schemas.py`,
`test_gemini_adapter.py`) proves, entirely offline: schema validity and strict
rejection of malformed output; citation faithfulness (unsupported sentences are
suppressed); conditional language for conditional pathways; rejection of
unsupported and claim-state-altering output; retry-once-then-fallback; and that a
disabled provider leaves the core deterministic product intact.

## Enabling live Gemini

Set in `.env` (local) or the Render dashboard (production):

```text
LLM_PROVIDER=gemini
LLM_API_KEY=<your Google AI Studio key>   # never commit this
LLM_MODEL=gemini-3.5-flash                 # override to any available model id
```

The key is read from the environment, never logged, and only public news and
evidence excerpts are transmitted. With no key set, enrichment stays disabled.

## Known follow-ups

- The exact Gemini model id and `responseSchema` shape should be confirmed
  against current Google documentation before relying on live calls; the adapter
  is provider-neutral and the endpoint/model are environment-configurable.
- Persisting enrichment results and traces to the database, and surfacing AI
  explanations in the API/frontend (behind the existing provenance labels),
  remain wiring steps; they are intentionally not prerequisites for the core
  product.
