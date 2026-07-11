# Milestone 0 runbook

Milestone 0 is a deterministic fixture spike. It invokes no news service, LLM,
or browser-facing API and contains no production data.

## Acceptance gate

```powershell
Copy-Item .env.example .env
uv sync --project backend --extra dev
uv run --project backend python scripts/bootstrap_milestone0.py
uv run --project backend python scripts/ripple_from_headline.py --fixture threat_only_hormuz
uv run --project backend pytest -v
```

The bootstrap command starts the Compose PostgreSQL service, waits for its
health check, applies the Alembic migration, and imports `energy_v0.json`
idempotently. The CLI must report `conditional_pathway`, `condition_met=false`,
and the unmet material-disruption condition for the threat-only fixture.

## Focused checks

```powershell
uv run --project backend ruff format --check backend/app backend/tests scripts
uv run --project backend ruff check backend/app backend/tests scripts
uv run --project backend mypy backend/app scripts
docker compose config
```

Frontend tooling is a no-UI baseline in this milestone:

```powershell
Push-Location frontend
npm.cmd install
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
npm.cmd run test:e2e
Pop-Location
```
