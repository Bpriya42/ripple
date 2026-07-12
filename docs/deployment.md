# Deployment runbook

Ripple deploys the FastAPI backend and managed Postgres to **Render** (via
`render.yaml`), the React SPA to **Vercel** (via `frontend/vercel.json`), and
runs the scheduled GDELT ingestion job on **GitHub Actions** (via
`.github/workflows/ingest.yml`) rather than a Render cron service — see
[cicd.md](cicd.md) for why. No secret values live in the repository; every
credential is supplied through the hosting dashboards or GitHub Actions
secrets.

## Prerequisites

- A Render account, a Vercel account, and this repository pushed to a Git
  remote both platforms (and GitHub Actions) can read.
- No API keys are required for Milestone 3. GDELT is free and needs no key. The
  Gemini `LLM_*` variables are introduced in Milestone 4 and stay unset here.

## Backend + database (Render)

1. In Render, choose **New → Blueprint** and point it at this repository. Render
   reads `render.yaml` and provisions two resources: `ripple-postgres`
   (database) and `ripple-api` (web service).
2. `DATABASE_URL` is wired automatically from `ripple-postgres`. The backend
   normalizes the `postgresql://` URL to the psycopg 3 driver at runtime.
3. Set `FRONTEND_ORIGIN` on `ripple-api` to your Vercel origin(s), comma
   separated, e.g. `https://ripple.vercel.app,https://ripple-preview.vercel.app`.
   This is the CORS allow-list; the frontend never receives backend secrets.
4. Free-tier web services can't run a separate pre-deploy step, so Alembic
   migrations run as the first part of the start command on every boot
   (`upgrade head` is idempotent). The service exposes `/health` for Render's
   health check.

## Scheduled ingestion (GitHub Actions)

Render has no free tier for cron jobs (metered, ~$1/month minimum), so the
30-minute GDELT ingestion tick runs as a GitHub Actions scheduled workflow
instead, at zero extra cost:

1. In Render, open `ripple-postgres` → **Connect** → copy the **External
   Database URL** (not the internal one used by `fromDatabase` — that host is
   only reachable from inside Render's network).
2. In GitHub: repo → **Settings → Secrets and variables → Actions** → add
   `PROD_DATABASE_URL` with that external URL.
3. `.github/workflows/ingest.yml` runs on a `*/30 * * * *` schedule (and via
   manual **Run workflow** dispatch), executing the same idempotent ingestion
   job the Render cron would have, against your production database.
4. Each tick uses a fresh timestamped run key, so it's recorded independently
   in `ingestion_runs`; a `failed` row is followed by a later `succeeded` row
   on the next tick.

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
2. Trigger the ingestion workflow once (GitHub → Actions → `ingest` →
   **Run workflow**). It should finish `succeeded` with a non-zero
   `records_seen`.
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
