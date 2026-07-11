# Ripple

Ripple is a desktop-first educational product for explaining evidence-backed
cross-border consequences of current energy news. It is not a forecasting
engine. The canonical specification is [Master Build Plan.md](Master%20Build%20Plan.md)
and the implementation contract is
[RIPPLE_COMPLETE_BUILD_HANDOFF.md](RIPPLE_COMPLETE_BUILD_HANDOFF.md).

## Local application

Requirements: Python 3.12+, `uv`, Node.js 22+, Docker, and Docker Compose.
The deterministic API and desktop-first React explorer serve explicitly marked
fixtures out of the box. Milestone 3 adds opt-in live GDELT ingestion (see
below); no LLM is invoked yet.

```powershell
Copy-Item .env.example .env
uv sync --project backend --extra dev
uv run --project backend python scripts/bootstrap_milestone1.py
uv run --project backend uvicorn app.main:app --reload
```

In another shell:

```powershell
Push-Location frontend
npm.cmd install
npm.cmd run dev
Pop-Location
```

Open `http://127.0.0.1:5173`. The Vite development proxy forwards `/api` to the
backend; production uses CORS (`FRONTEND_ORIGIN`) and a Vercel rewrite instead.

See `docs/milestone_2.md` for the frontend acceptance gate and complete test
commands.

## Live ingestion (Milestone 3)

Live GDELT ingestion is opt-in and isolated behind a provider interface. It maps
fresh energy headlines to curated nodes deterministically and always ingests
with `condition_met=false`, so no live claim is presented as an observed
outcome. Tests never touch the network; a recorded DOC API fixture drives them.

```powershell
# Inspect today's energy headlines (offline replay of the recorded fixture):
uv run --project backend python scripts/pull_gdelt_energy.py --dry-run
# Persist the recorded sample through the ingestion job:
uv run --project backend python -m app.jobs.ingest --provider gdelt --recorded data/fixtures/gdelt_doc_api_sample.json --run-key gdelt-recorded-smoke
```

Omit `--recorded` to fetch live from GDELT (no API key required). See
`docs/milestone_3.md` for the acceptance gate, `docs/deployment.md` for the
Render + Vercel deployment runbook, and `docs/cicd.md` for the CI/CD pipeline
(gated deploy on `main`).

## LLM enrichment (Milestone 4)

Enrichment is optional and disabled by default, so the deterministic product runs
with no model calls. The language model may only explain a claim the publication
policy already approved; it never assigns certainty or decides publication, must
preserve the exact claim state, and every generated sentence must be supported by
cited excerpts or the explanation is suppressed.

```powershell
# Run the pipeline offline with canned fixture responses:
uv run --project backend python scripts/explain_claim.py --demo
# Uses the configured provider (disabled -> deterministic fallback) otherwise:
uv run --project backend python scripts/explain_claim.py
```

To enable live Gemini, set `LLM_PROVIDER=gemini` and `LLM_API_KEY` (a Google AI
Studio key) in `.env` — never commit the key. See `docs/milestone_4.md`.
