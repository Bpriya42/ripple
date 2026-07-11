# Milestone 1 runbook

Milestone 1 is the deterministic backend core. It contains no live ingestion,
LLM provider, user account, or product frontend.

## Initialize and run

```powershell
uv sync --project backend --extra dev
uv run --project backend python scripts/bootstrap_milestone1.py
uv run --project backend uvicorn app.main:app --reload
```

## Mocked scheduled job

This finite command uses only the checked-in GDELT-shaped fixture and exits:

```powershell
uv run --project backend python -m app.jobs.ingest --run-key fixture-manual-v1
```

Rerunning the same key reports `already_processed=True` and creates no duplicate
story. Render can invoke the same finite module command as a Cron Job later;
deployment configuration remains a Milestone 3 concern.

## Contract and verification

```powershell
uv run --project backend python scripts/export_openapi.py
uv run --project backend ruff format --check backend/app backend/alembic backend/tests scripts
uv run --project backend ruff check backend/app backend/alembic backend/tests scripts
uv run --project backend mypy backend/app scripts
uv run --project backend pytest -v
```

The acceptance gate requires integration coverage for health, feed cursor
pagination, story detail, story ripples, concept ripples, edge evidence,
PostgreSQL caching, OpenAPI drift, and idempotent mocked ingestion. The
threat-only Hormuz fixture must remain a visible conditional pathway with its
unmet material-disruption condition.
