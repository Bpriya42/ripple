# Ripple

Ripple is a desktop-first educational product for explaining evidence-backed
cross-border consequences of current energy news. It is not a forecasting
engine. The canonical specification is [Master Build Plan.md](Master%20Build%20Plan.md)
and the implementation contract is
[RIPPLE_COMPLETE_BUILD_HANDOFF.md](RIPPLE_COMPLETE_BUILD_HANDOFF.md).

## Milestone 0

Requirements: Python 3.12+, `uv`, Docker, and Docker Compose. Node.js/npm are
needed only for the frontend tooling checks; Milestone 0 does not contain UI.

```powershell
Copy-Item .env.example .env
uv sync --project backend --extra dev
uv run --project backend python scripts/bootstrap_milestone0.py
uv run --project backend python scripts/ripple_from_headline.py --fixture threat_only_hormuz
uv run --project backend pytest -v
```

`bootstrap_milestone0.py` is the acceptance-gate setup command: it starts the
local PostgreSQL service, applies migrations, and idempotently imports the
fixture graph. See `docs/milestone_0.md` for the exact gate and troubleshooting.

The graph and story records used by the spike are explicitly marked fixtures.
No external service or LLM is invoked.
