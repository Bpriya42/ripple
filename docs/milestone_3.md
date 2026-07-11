# Milestone 3 — live ingestion and deployment readiness

Milestone 3 adds live GDELT ingestion and the configuration needed to deploy the
Milestone 1–2 system. All displayed causal claims still come from the
deterministic publication policy. Live stories are never asserted as observed
outcomes: they are ingested with `condition_met=false`, so their edges render as
conditional pathways until an evidence-grounded upgrade (deferred to Milestone
4). Fixtures remain explicitly marked and visibly distinct from live data.

## Delivered

- GDELT 2.0 DOC API adapter behind the existing `StoryProvider` interface, with
  networking isolated to `HttpGdeltDocClient` and an offline `RecordedGdeltDocClient`
  for tests. Articles are deduplicated by URL with aggregated themes.
- Deterministic linker (`app.services.linker`) that maps a story's GDELT themes
  to curated nodes using each node's `gdelt_tags`, preferring nodes that produce
  a ripple, with an order-independent, alphabetical tie-break.
- Keyword-based `event_status` classification (threat language takes precedence)
  that never sets `condition_met`.
- Transparent prominence reasons for live stories (recency, curated coverage,
  origin), stored on each story.
- Idempotent ingestion that owns its transactions: the run ledger is committed
  independently, so a failed run is durably recorded as `failed` (partial data
  rolled back) and a later run recovers. Structured logging on the CLI.
- Honest empty state: a live story that matches no curated node is stored and
  shown in the feed with no manufactured chain.
- CORS driven by `FRONTEND_ORIGIN`; `postgresql://` URLs normalized to psycopg 3.
- `scripts/pull_gdelt_energy.py` inspection spike (`--dry-run` replays the
  recorded fixture; live is opt-in and never persists).
- Deployment configuration: `render.yaml` (web + Postgres + ingestion cron),
  `frontend/vercel.json`, and `docs/deployment.md`. No secret values are checked
  in.

## Local acceptance gate

```powershell
uv run --project backend ruff format --check backend/app backend/alembic backend/tests scripts
uv run --project backend ruff check backend/app backend/alembic backend/tests scripts
uv run --project backend mypy backend/app scripts
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend pytest -v
uv run --project backend python scripts/export_openapi.py   # then: git diff --exit-code docs/openapi.json

# Offline live-path proof (no network):
uv run --project backend python scripts/pull_gdelt_energy.py --dry-run
uv run --project backend python -m app.jobs.ingest --provider gdelt --recorded data/fixtures/gdelt_doc_api_sample.json --run-key gdelt-recorded-smoke
```

The pytest suite proves, entirely offline, that: a mocked ingestion run persists
idempotently; a failed run is recorded as `failed` and a rerun recovers; the
feed serves live (non-fixture) stories; an Explorer response is cached; and every
live claim is a conditional pathway. Tests never perform network I/O.

## Deferred

Live LLM-assisted claim suggestions and evidence-grounded upgrades of live
stories (Milestone 4), production observability dashboards, mobile-specific
exploration, authentication, and comparison tools remain later milestones. The
actual Render/Vercel deploy is performed by the operator using the runbook; it
is not automated from this environment.
