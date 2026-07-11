# Ripple

Ripple is a desktop-first educational product for explaining evidence-backed
cross-border consequences of current energy news. It is not a forecasting
engine. The canonical specification is [Master Build Plan.md](Master%20Build%20Plan.md)
and the implementation contract is
[RIPPLE_COMPLETE_BUILD_HANDOFF.md](RIPPLE_COMPLETE_BUILD_HANDOFF.md).

## Local backend

Requirements: Python 3.12+, `uv`, Docker, and Docker Compose. Milestone 1 serves
explicitly marked fixtures through the deterministic FastAPI backend; it does
not perform live ingestion or invoke an LLM.

```powershell
Copy-Item .env.example .env
uv sync --project backend --extra dev
uv run --project backend python scripts/bootstrap_milestone1.py
uv run --project backend uvicorn app.main:app --reload
```

In another shell:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/feed?domain=energy&limit=10"
Invoke-RestMethod "http://127.0.0.1:8000/story/story.fixture.threat_only_hormuz/ripples"
uv run --project backend pytest -v
```

`bootstrap_milestone1.py` starts PostgreSQL, applies migrations, and
idempotently imports the graph and story fixtures. The generated API contract
is available at `/openapi.json` and checked in at `docs/openapi.json`.

See `docs/milestone_1.md` for the acceptance gate and cron-fixture command.
