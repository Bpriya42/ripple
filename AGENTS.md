# Ripple repository instructions

Treat `Master Build Plan.md` as the canonical product specification and
`RIPPLE_COMPLETE_BUILD_HANDOFF.md` as the implementation contract. Inspect
existing code before editing, make focused changes, run the relevant checks,
and report exact results.

## Causal publication rules

- Every displayed claim is sourced; unsupported claims are not shown.
- A valid mechanism is not proof that an event-specific outcome occurred.
- Conditional pathways are shown by default and name the unmet condition.
- Certainty and publication eligibility are deterministic, never assigned by an LLM.
- AI-suggested ordinary claims require two independent sources; high-impact or
  disruption claims require three.
- Preserve credible contradictions as contested or suppress the claim.
- Fixtures must be clearly labeled. Never invent production data.
- Never expose secrets or bypass tests with skip/only flags.

## Commands

```powershell
uv sync --project backend --extra dev
uv run --project backend ruff format --check backend/app backend/alembic backend/tests scripts
uv run --project backend ruff check backend/app backend/alembic backend/tests scripts
uv run --project backend mypy backend/app scripts
uv run --project backend pytest -v
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend python scripts/import_graph.py
uv run --project backend python scripts/import_story_fixtures.py
uv run --project backend python scripts/bootstrap_milestone1.py
uv run --project backend python scripts/export_openapi.py
uv run --project backend python -m app.jobs.ingest --run-key fixture-manual-v1
uv run --project backend uvicorn app.main:app --reload
uv run --project backend python scripts/ripple_from_headline.py --fixture threat_only_hormuz
uv run --project backend python scripts/bootstrap_milestone0.py
docker compose up -d postgres
Push-Location frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
npm.cmd run test:e2e
Pop-Location
```
