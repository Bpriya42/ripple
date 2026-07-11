# Deployment runbook

Ripple deploys the FastAPI backend, managed Postgres, and the scheduled GDELT
ingestion job to **Render** (via `render.yaml`), and the React SPA to **Vercel**
(via `frontend/vercel.json`). No secret values live in the repository; every
credential is supplied through the hosting dashboards.

## Prerequisites

- A Render account and a Vercel account.
- This repository pushed to a Git remote both platforms can read.
- No API keys are required for Milestone 3. GDELT is free and needs no key. The
  Gemini `LLM_*` variables are introduced in Milestone 4 and stay unset here.

## Backend + database + cron (Render)

1. In Render, choose **New → Blueprint** and point it at this repository. Render
   reads `render.yaml` and provisions three resources: `ripple-postgres`
   (database), `ripple-api` (web service), and `ripple-ingest` (cron job).
2. `DATABASE_URL` is wired automatically from `ripple-postgres`. The backend
   normalizes the `postgresql://` URL to the psycopg 3 driver at runtime.
3. Set `FRONTEND_ORIGIN` on `ripple-api` to your Vercel origin(s), comma
   separated, e.g. `https://ripple.vercel.app,https://ripple-preview.vercel.app`.
   This is the CORS allow-list; the frontend never receives backend secrets.
4. The web service runs Alembic migrations in its pre-deploy step and exposes
   `/health` for Render's health check.
5. `ripple-ingest` runs every 30 minutes with a unique timestamped run key, so
   each tick performs a fresh, idempotent ingestion recorded in
   `ingestion_runs`. A failed tick is recorded as `failed`; the next tick
   recovers on its own key.

## Frontend (Vercel)

1. In Vercel, **Import** this repository and set the project root to `frontend/`.
2. Vercel reads `frontend/vercel.json`. Edit the rewrite `destination` host from
   `REPLACE_WITH_RENDER_API_HOST` to your `ripple-api` host (e.g.
   `ripple-api.onrender.com`). The SPA calls the API through the same-origin
   `/api` prefix, so the API base URL is the only frontend configuration and no
   provider secret is ever bundled.
3. Deploy. Vercel builds with `npm run build` and serves `dist/`.

## Verifying a staging deployment (Milestone 3 gate)

1. `GET https://<ripple-api>/health` returns `{"status":"ok","database":"ok"}`.
2. Trigger `ripple-ingest` once (Render → the cron job → **Run now**). It should
   finish `succeeded` with a non-zero `records_seen`.
3. `GET https://<ripple-api>/feed?domain=energy` returns live, non-fixture
   stories with transparent prominence reasons.
4. Open a story in the Vercel app; the Explorer loads a cached ripple response
   and every live claim renders as a conditional pathway.
5. To confirm recovery, inspect `ingestion_runs`: any `failed` row is followed by
   a later `succeeded` row, and the feed continues to serve.

## Trust and copyright constraints preserved in production

- The frontend shows only headline, snippet, and a link out; full article text
  is never republished.
- Live stories are always ingested with `condition_met=false`, so no live claim
  is presented as an observed outcome.
- Fixtures remain flagged (`fixture=true`) and visibly distinct from live data.
