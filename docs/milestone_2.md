# Milestone 2 — product surface and causal explorer

Milestone 2 adds the desktop-first React application over the Milestone 1 API.
All displayed causal claims still come from the deterministic publication
policy. Fixture stories, effect-region markers, and concept presentation
metadata are explicitly labeled and do not represent production observations.

## Delivered

- Dense, cursor-paginated energy feed with loading, stale-refresh, empty, and
  API-error states.
- Six-second story reveal with a skip control and a static reduced-motion path.
- Three.js globe with country outlines, event-origin context, illustrative
  fixture clusters, camera movement, and manual orbit controls.
- Non-geographic causal rail, alternate branch replacement, synchronized
  certainty/time/category filters, and immediate evidence for every claim.
- Conditional pathways shown by default with the unmet condition named.
- Keyboard-operable text chain that repeats the same claim and evidence as the
  visual explorer.
- OpenAPI-generated TypeScript contract and CI drift check.

## Local acceptance gate

```powershell
uv run --project backend python scripts/bootstrap_milestone1.py
uv run --project backend ruff format --check backend/app backend/alembic backend/tests scripts
uv run --project backend ruff check backend/app backend/alembic backend/tests scripts
uv run --project backend mypy backend/app scripts
uv run --project backend pytest -v

Push-Location frontend
npm.cmd run generate:api
npm.cmd run format:check
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
npm.cmd run test:e2e
Pop-Location
```

The Playwright gate follows feed → threat-only Hormuz story → reveal skip →
claim edge → evidence → filter → alternate branch. A second browser test uses
the keyboard text chain and verifies the same conditional claim and evidence.

## Deferred

Live GDELT, LLM-assisted claim suggestions, production CORS, deployment,
mobile-specific exploration, authentication, and comparison tools remain later
milestones.
