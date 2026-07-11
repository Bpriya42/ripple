# Ripple

Ripple is a desktop-first educational product for explaining evidence-backed
cross-border consequences of current energy news. It is not a forecasting
engine. The canonical specification is [Master Build Plan.md](Master%20Build%20Plan.md)
and the implementation contract is
[RIPPLE_COMPLETE_BUILD_HANDOFF.md](RIPPLE_COMPLETE_BUILD_HANDOFF.md).

## Local application

Requirements: Python 3.12+, `uv`, Node.js 22+, Docker, and Docker Compose.
Milestone 2 serves explicitly marked fixtures through the deterministic API and
a desktop-first React explorer; it does not perform live ingestion or invoke an
LLM.

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

Open `http://127.0.0.1:5173`. The Vite development proxy keeps Milestone 2 local
without introducing the production CORS and deployment work reserved for
Milestone 3.

See `docs/milestone_2.md` for the acceptance gate and complete test commands.
