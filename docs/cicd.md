# CI/CD

`.github/workflows/ci.yml` runs three gate jobs in parallel on every push and
pull request, then a `deploy` job that only fires after all three pass **and**
the push is to `main`:

```
gitleaks ─┐
backend  ─┼─▶ deploy (main pushes only)
frontend ─┘
```

- **gitleaks** — secret scan.
- **backend** — migrate, import fixtures, OpenAPI drift check, ruff
  format/lint, mypy, pytest, offline GDELT dry-run, offline enrichment demo
  (`explain_claim.py --demo`, scripted provider, no network call).
- **frontend** — API-type drift check, format/lint, typecheck, vitest, build,
  Playwright e2e.
- **deploy** — POSTs to a Render deploy hook and a Vercel deploy hook. It does
  nothing on PRs or branches other than `main`, so production only updates
  once the full gate is green on `main`.

Deploys are triggered **only** by this job, not by Render/Vercel watching the
branch directly — this guarantees nothing broken reaches production, and
avoids a push triggering two competing deploys.

## One-time setup

### 1. Render deploy hook
Render dashboard → your web service → **Settings → Deploy Hook** → copy the
URL. Then **Settings → Auto-Deploy → No** (turn off native auto-deploy; the
Actions job is now the only trigger).

### 2. Vercel deploy hook
Vercel dashboard → your project → **Settings → Git → Deploy Hooks** → create
one (name it `ci`, branch `main`) → copy the URL. Then **Settings → Git →
disconnect automatic deployments for pushes** (or set the production branch to
something the repo never pushes to) so Vercel doesn't also deploy on its own.

### 3. Add the two URLs as GitHub secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|---|---|
| `RENDER_DEPLOY_HOOK_URL` | the Render hook URL from step 1 |
| `VERCEL_DEPLOY_HOOK_URL` | the Vercel hook URL from step 2 |

Deploy hook URLs are bearer-token-in-URL secrets (anyone with the URL can
trigger a deploy, but not read anything) — treat them like secrets, never
commit them, and store only in GitHub Actions secrets / the host dashboards.

### 4. Branch protection on `main`
Repo → **Settings → Branches → Add rule** for `main`:
- Require a pull request before merging
- Require status checks to pass before merging → select `gitleaks`,
  `backend`, `frontend`

This is what actually enforces the gate: without it, someone can push straight
to `main` and the `deploy` job still runs after CI passes, but nothing stopped
the push itself.

### 5. Ingestion secret
`.github/workflows/ingest.yml` runs the GDELT ingestion job on a `*/30 * * * *`
schedule — this replaces a Render cron service, since Render has no free cron
tier (metered, ~$1/month minimum). It needs one secret:

| Name | Value |
|---|---|
| `PROD_DATABASE_URL` | the **External Database URL** from Render's `ripple-postgres` → Connect (not the internal `fromDatabase` host, which is unreachable from outside Render) |

See [deployment.md](deployment.md#scheduled-ingestion-github-actions) for the
full walkthrough.

## Runtime secrets (application, not CI)

These are set directly on Render/Vercel, never in GitHub Actions:

- Render: `DATABASE_URL` (from the blueprint's managed Postgres),
  `FRONTEND_ORIGIN` (your Vercel URL), and, to enable live enrichment,
  `LLM_PROVIDER=gemini` + `LLM_API_KEY`.
- Vercel: the `/api` rewrite in `frontend/vercel.json` pointed at your Render
  API host.

See [deployment.md](deployment.md) for the full first-deploy walkthrough and
[milestone_4.md](milestone_4.md) for the LLM environment variables.

## Rollback

Render and Vercel both keep prior deploys and support one-click rollback in
their dashboards — that stays true even with hook-triggered deploys. To
re-deploy a specific commit, `git revert` it on `main`; the gate re-runs and
the `deploy` job pushes the reverted state forward (Render/Vercel deploy
whatever is on `main` at hook-trigger time, not a pinned SHA in the hook call).
