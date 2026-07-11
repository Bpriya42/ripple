# Ripple — Complete Build Handoff

This is a single self-contained handoff for the lead coding agent. Read the Build Agent Brief first, then Appendix A in full before changing code.

---

# Ripple â€” Build Agent Brief for GPT-5.6 Sol High

*Purpose: give this entire file and `Master Build Plan.md` to the coding agent. The agent must use them as its contract for building Ripple end-to-end.*

## 1. Operating contract

You are the lead implementation agent for **Ripple**, a desktop-first, informational product that explains the evidence-backed cross-border consequences of current energy news. You will build the application in a new Git repository, work in small verified increments, and leave a runnable, documented system.

Read these files in order before writing code:

1. `Appendix A: Master Build Plan` â€” canonical product and technical specification.
2. This brief â€” implementation decisions, operating rules, and acceptance criteria.
3. `AGENTS.md` â€” repository-local commands and durable implementation rules; create it during repository bootstrap if it does not exist.

If the two planning documents conflict, `Appendix A: Master Build Plan` wins **except** where this brief explicitly resolves a technical choice. Do not change product scope without recording the reason and proposing the change for approval.

### Non-negotiables

- Build an educational explanation product, not a forecasting engine.
- Never present an unsourced link as fact.
- Never state that an outcome has occurred merely because a known mechanism could apply.
- Conditional pathways are shown by default and state the unmet trigger condition.
- Certainty is derived by deterministic evidence rules; an LLM may explain it but may not assign it.
- The frontend never holds LLM-provider or database credentials.
- Do not add user accounts, mobile support, event comparison, or autonomous runtime agents in v1.
- Never use invented production data. Fixtures must be explicitly marked as fixtures.

## 2. Committed architecture

```text
Vercel
  React + TypeScript + Vite SPA
  React Router, TanStack Query, React Three Fiber / Three.js
        â”‚ HTTPS
Render
  FastAPI API + scheduled ingestion jobs
  SQLAlchemy + Alembic
        â”‚ private connection
Render Postgres
  relational graph, stories, evidence, caches
  pgvector when embeddings are introduced
```

### Technology choices

| Concern | Required choice |
|---|---|
| Frontend | React, TypeScript, Vite |
| Routing | React Router |
| Remote/cache state | TanStack Query |
| 3D Explorer | Three.js through React Three Fiber; use `@react-three/drei` only where it reduces complexity |
| Backend | FastAPI, Python 3.12+, Pydantic v2 |
| Persistence | Render Postgres, SQLAlchemy 2.x, Alembic |
| Graph authoring | Version-controlled JSON imported into Postgres |
| Retrieval | Postgres full-text search first; `pgvector` for embeddings when the linker needs it |
| LLM enrichment | Gemini 3.5 Flash free tier through the Gemini Interactions API; strict adapter and structured outputs |
| Background work | Render Cron Job initially; do not introduce Celery/Redis until a demonstrated need |
| Testing | pytest, Playwright, Vitest + React Testing Library |
| Deployment | Vercel frontend; Render FastAPI, Cron Job, and Postgres |

### Do not use in v1

- Neo4j, MongoDB, Supabase, or a separate vector database.
- A browser-to-database connection.
- A free-form LLM that returns unstructured causal claims.
- A multi-agent runtime in the user request path.
- A generic graph library as the primary Explorer; the visual experience is React Three Fiber plus a readable causal rail.

## 3. Repository bootstrap

Create this layout, then keep responsibilities separated:

```text
ripple/
â”œâ”€â”€ AGENTS.md
â”œâ”€â”€ README.md
â”œâ”€â”€ .env.example
â”œâ”€â”€ docker-compose.yml                 # local Postgres only
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ master_build_plan.md
â”‚   â”œâ”€â”€ build_agent_brief.md
â”‚   â”œâ”€â”€ architecture.md
â”‚   â”œâ”€â”€ api_contract.md
â”‚   â””â”€â”€ causal_publication_policy.md
â”œâ”€â”€ data/
â”‚   â””â”€â”€ graph/
â”‚       â””â”€â”€ energy_v0.json
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ db/
â”‚   â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ schemas/
â”‚   â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”‚   â”œâ”€â”€ ingest/
â”‚   â”‚   â”‚   â”œâ”€â”€ linker/
â”‚   â”‚   â”‚   â”œâ”€â”€ graph/
â”‚   â”‚   â”‚   â”œâ”€â”€ evidence/
â”‚   â”‚   â”‚   â”œâ”€â”€ reasoning/
â”‚   â”‚   â”‚   â””â”€â”€ ranking/
â”‚   â”‚   â””â”€â”€ main.py
â”‚   â”œâ”€â”€ alembic/
â”‚   â”œâ”€â”€ tests/
â”‚   â””â”€â”€ pyproject.toml
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ features/feed/
â”‚   â”‚   â”œâ”€â”€ features/explorer/
â”‚   â”‚   â”œâ”€â”€ routes/
â”‚   â”‚   â””â”€â”€ test/
â”‚   â”œâ”€â”€ e2e/
â”‚   â””â”€â”€ package.json
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ import_graph.py
â”‚   â””â”€â”€ pull_gdelt_energy.py
â”œâ”€â”€ render.yaml
â””â”€â”€ .github/workflows/ci.yml
```

Create `AGENTS.md` with:

- commands for backend tests, frontend tests, lint/type checks, Playwright, migrations, graph import, and local startup;
- the no-overclaim causal rules above;
- instruction to inspect existing code before editing, make focused changes, run relevant checks, and report exact verification results;
- instruction to treat `Appendix A: Master Build Plan` as canonical;
- instruction not to expose secrets or bypass tests with `skip`/`only` flags.

Use `.env.example` with names onlyâ€”never real values:

```text
DATABASE_URL=
FRONTEND_ORIGIN=http://localhost:5173
GDELT_BASE_URL=
LLM_PROVIDER=gemini
LLM_API_KEY=
LLM_MODEL=gemini-3.5-flash
```

## 4. Data and API contract

Implement migrations and typed schemas for at least:

- `nodes`, `node_aliases`, `edges`, `evidence_sources`, `edge_evidence`;
- `stories`, `story_sources`, `story_node_matches`;
- `event_claim_resolutions`, `ripple_cache`, and `ingestion_runs`.

Use UUID primary keys internally; retain stable public slugs such as `commodity.oil`. Store timestamps in UTC. Add foreign keys, uniqueness constraints, indexes for feed ordering, story-to-node lookup, edge traversal, and evidence lookup.

Every returned story-specific edge must include:

```json
{
  "edge_id": "...",
  "story_id": "...",
  "event_status": "threat_only | disruption_confirmed | ...",
  "required_condition": "...",
  "condition_met": false,
  "claim_state": "observed_effect | established_mechanism | emerging_signal | conditional_pathway | not_shown",
  "certainty": "established | emerging | speculative",
  "certainty_reasons": ["two independent direct sources", "curated mechanism"],
  "provenance": "curated | ai_suggested",
  "evidence": [],
  "contested": false
}
```

Implement and document:

- `GET /health`
- `GET /feed?domain=energy&limit=&cursor=`
- `GET /story/{story_id}`
- `GET /story/{story_id}/ripples`
- `GET /concept/{node_slug}/ripples`
- `GET /edge/{edge_id}`

Use OpenAPI-generated schemas as the contract. The frontend must consume typed client models generated or hand-maintained from those schemas; do not duplicate untyped response shapes.

## 5. Causal publication engine

Implement this deterministically before any LLM integration.

### Required pipeline

1. Normalize a story and extract only attributable facts.
2. Map story entities/themes to known graph nodes.
3. Traverse curated graph edges to a bounded depth (default 2; maximum 3).
4. For each edge, evaluate whether the event meets its `required_condition`.
5. Apply the publication policy below.
6. Return the main path, optional credible branches, evidence, and explanation-ready structured data.

### Publication policy

| Situation | Required `claim_state` | Display behavior |
|---|---|---|
| Direct event-specific evidence of the outcome | `observed_effect` | State the observed relationship with attribution |
| Curated mechanism; condition met; no direct outcome evidence | `established_mechanism` | Explain the mechanism; do not assert the final outcome occurred |
| Curated mechanism; required condition not met | `conditional_pathway` | Visible by default; explicitly state the condition |
| Source-grounded AI candidate with adequate evidence | `emerging_signal` | Visibly labeled emerging and AI-suggested |
| Inadequate, contradictory, or unsupported evidence | `not_shown` | Do not include in the default Explorer |

### Evidence rules

- AI-suggested ordinary claims require at least **two independent sources**.
- High-impact or disruption claims require at least **three independent sources**.
- A source copied/syndicated from another outlet is not independent.
- A credible contradiction either marks the claim `contested` with both views or suppresses it; do not average away disagreement.
- Certainty is computed from provenance, source independence, directness, recency, corroboration, and contradiction. Store the reasons used.
- The UI may filter by claim state, certainty, provenance, severity, consequence type, and lag; conditional pathways are enabled by default.

Write unit tests for every row of this policy table, including the threat-only Hormuz scenario.

## 6. LLM and prompt architecture

Do not add the Gemini provider implementation until deterministic traversal, evidence rules, and fixtures are passing. Build a provider interface with a disabled local/mock implementation first, then add Gemini 3.5 Flash through the Gemini Interactions API.

### Gemini data boundary

- Send Gemini only the minimum necessary public news excerpts, public evidence excerpts, stable graph definitions, and anonymous system metadata.
- Never send user data, credentials, cookies, access tokens, unpublished research, internal notes, or complete licensed article text.
- Store only the validated structured result, evidence IDs, prompt version, model ID, and evaluation trace needed for auditability.
- Do not use Gemini search grounding as the source of record. Ripple retrieves, stores, and validates its own evidence before model invocation.

### LLM boundaries

The LLM may:

- map an ambiguous story to candidate existing nodes;
- summarize approved source excerpts in plain language;
- propose a candidate edge only with retrieved evidence;
- explain the rule-derived claim state and certainty reasons.

The LLM may not:

- create an uncited fact, number, event status, source, or causal edge;
- decide certainty or publication eligibility;
- treat a known mechanism as proof that an event-specific outcome occurred;
- hide contradictory evidence;
- return free-form production output.

### Required structured-output contracts

Use JSON Schema / Pydantic models with strict validation. Retry once only for schema-invalid output; otherwise fall back to deterministic behavior and log the failure.

#### A. Event fact extraction prompt

```text
SYSTEM
Extract only facts explicitly stated in the supplied story excerpts. Do not infer causes, effects, motives, future outcomes, or missing details. For every fact, include one or more exact supporting excerpt IDs. If a fact is uncertain in the source, preserve that uncertainty. Return only the required JSON schema.

USER
Story metadata: {story_metadata}
Source excerpts: {numbered_excerpts}
Required schema: {event_fact_schema}
```

#### B. Applicability assessment prompt

```text
SYSTEM
Assess whether the listed event facts meet the required condition of a known causal mechanism. A mechanism being valid does not prove its outcome has occurred. If the condition is unmet, return conditional_pathway. If evidence is insufficient or contradictory, return not_shown. Do not assign certainty; report only evidence facts, condition status, contradictions, and a permitted claim state. Cite excerpt IDs for every conclusion. Return only the required JSON schema.

USER
Known mechanism: {edge_definition}
Required condition: {required_condition}
Event facts: {validated_event_facts}
Evidence excerpts: {numbered_excerpts}
Required schema: {applicability_schema}
```

#### C. Explanation prompt

```text
SYSTEM
Write a concise public explanation using only the approved claim record and cited evidence excerpts. Preserve the exact claim state. Use conditional language when claim_state is conditional_pathway. Do not add facts, quantities, causal steps, forecasts, or certainty language not present in the input. Mention the unmet condition when one exists. Return only the required JSON schema.

USER
Approved claim record: {validated_claim_record}
Evidence excerpts: {numbered_excerpts}
Required schema: {explanation_schema}
```

#### D. Faithfulness review prompt

```text
SYSTEM
For each sentence in the proposed explanation, decide whether the supplied excerpts directly support it. Flag unsupported, overstated, causal, temporal, numeric, or certainty claims. Do not repair the explanation. Return only the required JSON schema.

USER
Proposed explanation: {draft}
Approved claim record: {validated_claim_record}
Evidence excerpts: {numbered_excerpts}
Required schema: {faithfulness_review_schema}
```

Only publish generated prose when all sentences are supported and the deterministic policy gate permits the claim.

## 7. Frontend implementation

Build the following screens and states using fixture data before live ingestion:

### Dense live-news board

- Dense cards: headline, timestamp, origin location, representative sources, domain, and transparent prominence reasons.
- Cursor pagination; loading, empty, stale-data, and API-error states.
- No animated globe previews in the feed.
- Curated concept entry points when no fresh energy stories are available.

### Story reveal and Explorer

- Desktop/WebGL-only v1.
- Charcoal base; amber for active/evidence-supported paths; red only for disruption severity.
- A 5â€“8 second guided story reveal of the main evidence-backed path; directed camera; **Skip to explore** control.
- Globe: country pins at global scale; subtle country surface highlighting on zoom; expandable regional clusters; camera flies to selected region.
- Causal rail: compact overlay by default; expandable; carries readable non-geographic nodes and path text.
- Alternatives are selectable branches on the globe; they replace the active causal rail and evidence selection.
- Immediate evidence panel on edge selection.
- Filters synchronize globe and causal rail.
- Keyboard alternative: text causal chain, tab-accessible selection, and no dependence on color/motion/sound.
- Respect `prefers-reduced-motion`; reveal must have an immediate static equivalent.

Do not block Phase 0/1 on photorealistic terrain or visual polish. The visual prototype must be functional, deterministic with fixtures, and testable.

## 8. Implementation sequence and acceptance gates

### Milestone 0 â€” Repository and deterministic spike

- Bootstrap repository, formatting, linting, tests, local Docker Postgres, migrations, fixture graph, and `AGENTS.md`.
- Implement `energy_v0.json` with at least 10 sourced edges.
- Implement a CLI that maps one fixture headline to a bounded, sourced ripple chain.

**Gate:** one command initializes the database/imports fixtures; one command runs the CLI; tests prove the threat-only example becomes a conditional pathway.

### Milestone 1 â€” Backend core

- Implement API, database models, graph import, bounded traversal, publication-policy engine, feed fixtures, and OpenAPI contract.
- Add cache abstraction backed by Postgres first.
- Add a Render Cron Job entry point that can run safely and idempotently; use a mocked GDELT response in tests.

**Gate:** FastAPI integration tests cover feed, story, ripple, concept, and evidence endpoints; no endpoint emits an unsupported claim.

### Milestone 2 â€” Frontend functional MVP

- Implement feed, API client, story route, static/reduced-motion reveal, Three.js globe prototype, causal rail, immediate evidence panel, filters, and empty/error states.
- Use Playwright to test the key path: feed â†’ story â†’ skip/reveal â†’ edge â†’ evidence â†’ filter â†’ branch.

**Gate:** production build succeeds; Playwright passes; keyboard text-chain route exposes the same claim/evidence data.

### Milestone 3 â€” Live ingestion and deployment readiness

- Implement GDELT adapter, normalization, deduplication, ranking explanations, idempotent persistence, observability, CORS, health endpoint, Render/Vercel configs, and deployment documentation.
- Keep full article text out of the public frontend; show headline/snippet/link-out only.

**Gate:** a staging deployment can ingest safely, serve a feed, open a cached Explorer response, and recover from a failed ingestion run.

### Milestone 4 â€” Gemini enrichment extension

- Implement the Gemini 3.5 Flash adapter through the Gemini Interactions API, strict structured outputs, prompt fixtures, faithfulness evaluator, traces, and suppression/fallback behavior.
- Do not make LLM output a prerequisite for core product functionality.

**Gate:** prompt/eval suite proves schema validity, citation faithfulness, conditional language, and rejection of unsupported claims.

## 9. How to use agents, skills, and tools

Use high-reasoning effort for architecture, database migrations, causal-policy code, security-sensitive work, and final integration. Use lower-cost models only for tightly scoped mechanical work after the contract is stable.

If the environment supports subagents, use them only for bounded, non-overlapping tasks:

| Role | Scope | Write permission |
|---|---|---|
| Lead agent | Plans, integrates, resolves conflicts, runs final verification | Yes |
| Research/recon agent | Reads docs, APIs, package constraints, and reports findings | No |
| Frontend agent | Works only in `frontend/` after API contract is stable | Yes, frontend only |
| Backend agent | Works only in `backend/`, `scripts/`, and migrations | Yes, backend only |
| Test/review agent | Inspects changes, runs tests, reports defects; does not redesign scope | No |

Never let two agents modify shared contracts, migrations, lock files, deployment files, or the same directory simultaneously. The lead agent owns API schemas, migrations, and merges.

Create reusable, repository-local workflows/skills only after a workflow repeats. Useful candidates:

- `graph-fixture-review`: validates node/edge JSON, citations, required conditions, and duplicate IDs;
- `causal-policy-eval`: runs fixture claims through the deterministic publication policy and prompt-eval suite;
- `release-check`: runs formatting, type checks, unit/integration/E2E tests, migration smoke test, and secret scan.

If the coding environment supports skills, store each workflow with concise instructions and scripts. If it does not, provide equivalent `scripts/` commands and document them in `AGENTS.md`; do not block the build on agent-platform features.

Use tools deliberately:

- inspect the repository before edits;
- use official documentation for dependencies and deployment configuration;
- use browser automation for real UI verification;
- use migrations, seed/import scripts, and CIâ€”not manual database changesâ€”as the reproducible path;
- use git commits at completed milestone boundaries with descriptive messages;
- keep secrets in environment variables and add secret scanning to CI.

## 10. Exact first prompt for GPT-5.6 Sol High

```text
You are the lead implementation agent for Ripple. Read docs/master_build_plan.md and docs/build_agent_brief.md completely before making changes. Treat the master plan as canonical and the brief as the implementation contract.

First, inspect the repository and report: (1) existing files and their purpose, (2) missing prerequisites, (3) a milestone-by-milestone implementation plan mapped to the brief, (4) commands you will use to verify each milestone, and (5) assumptions or blockers. Do not write application code yet.

After presenting the plan, begin Milestone 0 only. Create the repository baseline, AGENTS.md, local development setup, database migrations, fixture graph, deterministic causal-publication policy, and tests. Do not build the LLM integration, live GDELT ingestion, or final visual polish in this milestone.

Work in focused commits. Before every commit, run the relevant checks and report their exact results. Do not invent sources, endpoints, credentials, production data, or unresolved product decisions. Stop and ask for direction when a requirement materially conflicts with the contract.
```

For later work, use one milestone prompt at a time, always including the acceptance gate from Section 8. Do not ask the model to "build everything" in one unreviewed pass.

## 11. Model/provider findings

### GPT-5.6 Sol High

Use it as the primary lead coding model for this project. Official documentation lists a 1,050,000-token context window, structured outputs, tool use, skills, MCP, and apply-patch support; it is well suited to reading both planning documents and coordinating staged work. It is not free through the API: current listed API pricing is $5/M input tokens and $30/M output tokens. See [GPT-5.6 Sol documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol) and the [GPT-5.6 announcement](https://openai.com/index/gpt-5-6/).

### Gemini runtime provider

Gemini 3.5 Flash is the chosen v1 runtime provider. Its free tier supports thinking and structured outputs, which are required for Ripple's source-bounded enrichment workflow. Calls are restricted to public news/evidence excerpts because Google's free tier states that submitted content may be used to improve its products. Use the Gemini Interactions API and strict JSON-schema output; never let search grounding replace Ripple's own evidence pipeline. See [Gemini 3.5 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash), [Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview), and [pricing](https://ai.google.dev/gemini-api/docs/pricing).

### GLM

GLM can be used as a secondary coding/review model if its tool integration suits the operator, but the official GLM Coding Plan is **not free**: its published entry plan is $18/month and it requires a subscription/API key. It supports coding-tool integrations, including Claude Code-compatible workflows. See the [GLM quick start](https://docs.z.ai/guides/overview/quick-start) and [Coding Plan](https://z.ai/subscribe?invitedialog=true).

### Grok

Grok's consumer app has a free tier, but this should not be confused with a free production API. The xAI API is usage-billed; current official pricing lists Grok 4.3 at $1.25/M input tokens and $2.50/M output tokens. Do not use the consumer web product as an unattended coding or application-runtime dependency. See [xAI pricing](https://docs.x.ai/developers/pricing) and the [Grok 4.3 model page](https://docs.x.ai/developers/models/grok-4.3).

### Recommendation

- Use GPT-5.6 Sol High as lead planner/implementer and final reviewer.
- Optionally use GLM only as a paid, independent second-opinion coding reviewer.
- Use Gemini 3.5 Flash as the v1 runtime enrichment provider behind a strict adapter.
- Keep the adapter provider-neutral enough to add a paid provider after benchmark results warrant it.

## 12. Definition of done

The first complete v1 is done only when:

- a new developer can clone the repository, configure documented environment variables, start local dependencies, migrate/import fixtures, and run the application;
- the feed, story reveal, Explorer, causal rail, evidence panel, filters, and required empty/error/accessibility states work with fixtures;
- the backend implements and tests the causal publication policy;
- the UI never labels a conditional pathway as an observed effect;
- all lint, type, unit, integration, migration, and E2E checks pass in CI;
- Vercel and Render deployment configuration is present and documented;
- every source-bearing UI element links out and paywalls are visibly marked;
- README and architecture/API/runbook documents match the implementation.


---

# Appendix A: Master Build Plan

# Ripple â€” Master Build Plan (Ground Truth v1.0)

*Owner: Priya Balakrishnan Â· Last updated: July 2026*

> **Purpose of this document.** This is the single source of truth for the Ripple project. Every other file, skill, tool, or spec is built off the information here. When something changes, change it here first, then propagate. If two documents disagree, this one wins.

---

## 0. How to use this document

- **Sections 1â€“4** = what we're building and why (stable; changes rarely).
- **Sections 5â€“12** = how it works: experience, architecture, data, stack, AI, trust, design (the buildable core).
- **Sections 13â€“16** = quality, risk, roadmap.
- **Sections 17â€“19** = repo structure, open decisions, next steps.
- Keep a changelog at the bottom.

---

## 1. Product in one line

**Ripple is an explorable, near-real-time map of how the world is connected: click a news event, policy, country, or commodity and see how it ripples out to affect other places and things â€” at home and abroad â€” with the reasoning, evidence, and certainty behind every link.**

---

## 2. Problem & why now

People read a headline and rarely see the second- and third-order consequences â€” especially across borders (a strait closure â†’ oil prices â†’ inflation in importer nations â†’ food stress). These ripple effects are **real and well-documented** by economists (monetary/policy spillovers, global value-chain contagion, chokepoint effects), but that knowledge is locked in academic papers, not accessible to ordinary readers.

**Why now:** (a) fresh global news + entity tagging is now free and real-time (GDELT); (b) LLMs make it feasible to explain complex causal chains in plain language and ground them in sources; (c) products like Ground News have proven public appetite for smarter, more transparent news tools.

---

## 3. Landscape & differentiation

| Category | Examples | What they do | What they miss (our gap) |
|---|---|---|---|
| News aggregation / bias | **Ground News** | Cluster a story across outlets; show bias, factuality, blindspots | Coverage, not **consequences** |
| Policy simulation | PolicyEngine, OpenFisca, PSL | Model tax/benefit reforms numerically | Expert-facing; single-country; not news-driven |
| Anti-corruption / spending | Open Contracting, Cardinal | Red-flag procurement data | Narrow to procurement; not causal ripples |
| Global event data | **GDELT** | Real-time global news + knowledge graph | Raw data, no consequence explanation for humans |
| Academic spillover research | value-chain / spillover papers | Rigorous causal mechanisms | Inaccessible to the public |

**Ripple's one-sentence differentiation:** *Ground News maps coverage; Ripple maps consequences* â€” turning established cross-border cause-effect knowledge into something an ordinary person can explore.

---

## 4. Product definition & scope

- **Type (v1):** purely **informational / educational**. Shows *how things affect things*. **No prediction claims in v1** (prediction is a possible later layer).
- **Primary user (v1):** curious public, students, advocates, journalists. Designed so an NGO/gov/researcher can grow into it later.
- **Job-to-be-done:** *"I read this news â€” help me understand what it actually affects, and why, with evidence I can trust."*
- **North-star feel:** *"I had no idea that affects this â€” and now I understand why."*

**In scope (v1):** fresh news feed (one domain), clickable stories, home-ring + global-ring ripple map, evidence/certainty panel per link, hybrid curated+LLM knowledge.

**Out of scope (v1):** prediction/forecasting, all domains at once, full bias analytics, user accounts, mobile app, institutional dashboards.

---

## 5. Core experience & user flows

### Primary flow
1. **Browse** â€” a feed of fresh headlines (GDELT-fed, ~15-min fresh), filtered to the v1 domain, optionally with source/bias context (Ground News-style chips).
2. **Pick a story** â€” e.g. *"Iran threatens to close the Strait of Hormuz."*
3. **See the ripples** â€” a short, guided 5â€“8 second cinematic story reveal introduces the strongest evidence-backed causal chain. A Three.js globe shows where effects land; a companion causal rail states what happens and why. The user can always choose **Skip to explore**.
   - At world scale, affected countries appear as glowing pins; when zoomed in, the affected country surface is subtly highlighted.
   - When many countries are affected, effects begin as expandable regional clusters; selecting a region flies the camera to it and reveals country-level effects.
   - After the reveal, depth is user-controlled (expand one hop at a time) and credible alternative paths appear as selectable globe branches.
4. **Click a link (edge)** â€” panel shows: plain-language **mechanism (why)**, **direction**, **strength**, **lag**, **evidence/sources**, **certainty** (established / emerging / speculative), and whether it's **curated** or **AI-suggested**.
5. **Wander** â€” follow chains node to node; jump to any node via search (free exploration).

### Secondary flows
- Start from a **node** (e.g. "oil price") instead of a story and see what affects it / what it affects.
- **Share** a specific ripple view (URL encodes the node + expansion state).

---

## 6. System architecture

### The core insight: two layers linked
Separate what changes **fast** from what changes **slowly**.

- **Layer A â€” Fast news stream (volatile):** ingest fresh, entity-tagged news. Never hand-curated. Source: GDELT.
- **Layer B â€” Slow mechanism graph (stable):** curated + LLM-extended cause-effect relationships ("how the world works"). Maintained slowly; the trust backbone.
- **The Linker:** map a fresh story onto graph nodes (via its themes/entities/locations), then **traverse** the graph to produce the ripple map. RAG grounds every explanation in real text.

### Component diagram (logical)
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                         FRONTEND (React/TS)                   â”‚
â”‚   Headline feed  â”‚  Ripple graph view  â”‚  Evidence panel      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–²â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–²â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–²â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                â”‚ REST/JSON      â”‚              â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                         BACKEND API (FastAPI)                 â”‚
â”‚  /feed   /story/{id}   /ripples/{node}   /edge/{id}           â”‚
â””â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
    â”‚               â”‚                  â”‚              â”‚
â”Œâ”€â”€â”€â–¼â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ NEWS  â”‚   â”‚  LINKER /       â”‚  â”‚ MECHANISM    â”‚  â”‚ REASONING   â”‚
â”‚ INGESTâ”‚   â”‚  ENTITY MAPPER  â”‚  â”‚ GRAPH STORE  â”‚  â”‚ (LLM layer) â”‚
â”‚(GDELT)â”‚â”€â”€â–¶â”‚ storyâ†’nodes     â”‚â”€â–¶â”‚ nodes+edges  â”‚â—€â”€â”‚ RAG, decomp,â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚ (GKG tags+embed)â”‚  â”‚ (JSON/SQLite â”‚  â”‚ link-gen,   â”‚
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚  â†’Neo4j)     â”‚  â”‚ explanation â”‚
                                 â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                        â”‚              â”‚
                                 â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”
                                 â”‚  EVIDENCE / RETRIEVAL STORE  â”‚
                                 â”‚  article text + citations    â”‚
                                 â”‚  (BM25 + embeddings)         â”‚
                                 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**Implementation note:** the diagram's mechanism-graph label reflects the early evolution. For v1 production, the graph store is Render Postgres; version-controlled JSON is used only for curated-graph authoring/import.

### Data flow (a story click)
`story_id â†’ Linker maps to graph node(s) â†’ traverse edges N hops â†’ for each edge, attach curated evidence OR generate grounded link via LLM+RAG â†’ return ripple subgraph (nodes+edges+evidence+certainty) â†’ frontend renders map â†’ user clicks edge â†’ evidence panel`

---

## 7. Data model

### Node
```json
{
  "id": "commodity.oil",
  "type": "Event | Policy | Country | Commodity | Sector | Outcome",
  "label": "Global oil price",
  "aliases": ["crude", "brent", "WTI"],
  "gdelt_tags": ["ECON_OILPRICE", "..."],   // for story mapping
  "metadata": { "unit": "USD/barrel", "notes": "" }
}
```

### Edge (the heart of the trust model)
```json
{
  "id": "edge.hormuz_disruption__oil_price",
  "from": "event.hormuz_disruption",
  "to": "commodity.oil",
  "direction": "increases",              // increases | decreases | destabilizes | ...
  "strength": "high",                    // high | medium | low  (or range)
  "lag": "days",                         // immediate | days | months | years
  "mechanism": "â‰ˆ30% of seaborne oil transits Hormuz; a supply threat raises crude prices.",
  "certainty": "established",            // established | emerging | speculative
  "provenance": "curated",               // curated | ai_suggested
  "evidence": [
    {"title": "...", "url": "https://...", "type": "study|historical|theory"}
  ],
  "contested": false,
  "contested_views": []                  // if true, both sides here
}
```

### Story (from news layer)
```json
{
  "id": "story.2026xxxx.hormuz",
  "headline": "Iran threatens to close the Strait of Hormuz",
  "published": "2026-07-10T...",
  "sources": [{"outlet":"...","url":"...","bias":"...","factuality":"..."}],
  "gkg_themes": ["..."], "locations": ["Iran","Strait of Hormuz"],
  "entities": ["..."],
  "mapped_nodes": ["event.hormuz_disruption"]   // filled by Linker
}
```

### Event-specific claim resolution (returned with a ripple)

The stable graph edge describes a durable mechanism. A story-specific resolution decides whether that mechanism is activated by this event and how it may be described to users.

```json
{
  "edge_id": "edge.hormuz_disruption__oil_price",
  "story_id": "story.2026xxxx.hormuz",
  "event_status": "threat_only",
  "required_condition": "material disruption to Hormuz transit",
  "condition_met": false,
  "claim_state": "conditional_pathway",
  "certainty_score": 0.72,
  "certainty": "established",
  "evidence_ids": ["source_12", "source_47"],
  "contradictory_evidence_ids": [],
  "publish": true
}
```

`claim_state` is one of `observed_effect`, `established_mechanism`, `emerging_signal`, `conditional_pathway`, or `not_shown`. The system must never describe an outcome as observed merely because a known mechanism could apply.

---

## 8. Data sources (all free / cheap)

| Need | Source | Notes |
|---|---|---|
| Fresh global news + events | **GDELT 2.0** (DOC API + GKG) | Free, no key, 15-min updates, 100+ countries, pre-tagged themes/entities/locations |
| Outlet bias/factuality | AllSides / Media Bias-Fact Check-style public ratings | Attribute; don't imply self-rated |
| Economic mechanism evidence | World Bank, IMF, academic papers (spillovers, value chains), FEWS NET/FAOSTAT for food/energy | For curated edge citations |
| Commodity/energy context | World Bank commodity data, EIA | v1 domain = energy/commodities |
| (Future) prediction data | World Bank indicators, expenditure surveys | Not v1 |

---

## 9. Tech stack

| Layer | Choice | Why |
|---|---|---|
| News ingestion | GDELT 2.0 API (Python client) | Free, real-time, tagged |
| Mechanism graph store | Versioned JSON â†’ **Render Postgres** | JSON supports Phase 0 authoring/import; managed Postgres is the v1 production source of truth |
| Entity/theme â†’ node mapping | GDELT GKG tags + embedding similarity | Reuses tags; cheap |
| Retrieval | BM25 + embeddings (`pgvector` in Render Postgres) | Priya's CIIR/RAG stack, re-pointed; keep relational data and embeddings together in v1 |
| Reasoning / orchestration | **LangGraph** (query decomposition, link-gen, explanation) | Priya already knows it |
| LLM | **Gemini 3.5 Flash free tier** via the Gemini Interactions API, cached aggressively | Free hosted reasoning, thinking, and structured output for public-evidence-only enrichment |
| Backend | **FastAPI** (Python) | Priya's stack |
| Frontend | **React + TypeScript** | Priya's stack |
| Graph visualization | **Three.js / React Three Fiber** + companion causal rail | Cinematic, geographic 3D Explorer; readable causal explanation remains outside the globe |
| Charts (if needed) | Recharts / uPlot | Priya has uPlot experience |
| Frontend hosting | **Vercel** | Deploy the React/Vite SPA globally with preview deployments |
| Backend + workers | **Render** | Host FastAPI and scheduled GDELT ingestion/cache-refresh jobs |
| **Est. running cost** | **~$0â€“25/month** | LLM calls only; GDELT free |

---

## 10. The AI / reasoning layer

Borrows the **method** from Hindsight (not its code): graph traversal + query decomposition + RAG + faithfulness evaluation, rebuilt for news.

1. **Storyâ†’node mapping (Linker):** GDELT tags + embeddings match a story to existing graph nodes; if none, create a candidate node.
2. **Traversal:** walk curated edges outward N hops to build the ripple subgraph.
3. **Event applicability:** for each candidate edge, extract only attributable story facts; compare them with the edge's required conditions; and classify the result as observed, established, emerging, conditional, or not shown.
4. **Gap-filling (LLM):** where the graph lacks an edge the story implies, the LLM proposes a **grounded** candidate edge (RAG over article + evidence), tagged `ai_suggested`. Human can later promote to `curated`.
5. **Evidence rules:** derive certainty and publication eligibility from rule-based evidence criteria, including source independence, directness, recency, contradiction, and impact severity. Require at least two independent sources for ordinary AI-suggested claims and three for high-impact/disruptive claims; a credible contradiction marks the link contested or suppresses it.
6. **Explanation:** LLM writes the plain-language "why" and explains the rule-derived status strictly from approved, cited evidence â€” **never invents numbers or claims without a source.**
7. **Evaluation harness (Priya's edge):** LLM-as-judge + faithfulness checks that every generated explanation matches its cited source; flag hallucinations.

---

## 11. Trust & epistemics layer (the "good for people" core)

Non-negotiables, built from day one:
- **Curated vs AI-suggested is always visibly distinct** (color/badge). Never blur them.
- **Every claim is sourced or it isn't shown.**
- **Emerging AI-suggested links remain source-grounded**; emerging means limited or unsettled evidence, never unsupported speculation.
- **LLM data boundary:** Gemini receives only the minimum necessary public news excerpts and public evidence metadata. It never receives user data, credentials, unpublished material, or complete licensed article text.
- **Conditional pathways are visible by default.** They state the unmet trigger condition plainly and are never phrased as an outcome that has already occurred.
- **Certainty is rule-derived.** The LLM may explain the underlying evidence criteria but may not assign certainty on its own.
- **Certainty is first-class** (established / emerging / speculative), not fine print.
- **Correlation â‰  causation shown explicitly** (edge `type`: study / historical / theory).
- **Strength + lag**, not just yes/no ("strongly, within weeks" vs "weakly, over years").
- **Contested links shown as contested**, with both views.
- **Copyright:** headlines + short snippets + link out (Ground News model); never republish full articles.

Relevant to Priya's background: BlueDot AI-safety cert + Responsible/Trustworthy AI coursework = applied trustworthy-AI design.

---

## 12. Design / UX plan

### Design north star

**Ripple is an explanation tool first and a graph tool second.** Its visual system makes cross-border consequences tangible while keeping every claim readable, sourced, and clearly qualified.

### Screens (v1)

1. **Live news board** â€” a dense, fast-scanning global-energy board. Story prominence is a transparent blend of recency, estimated global impact, and the richness/quality of available ripple evidence. Cards show headline, time, place, source context, and compact explanations such as *recent*, *high cross-border impact*, and *strong ripple evidence*. The feed contains no animated globe previews. If fresh relevant news is unavailable, it offers curated concept entry points such as *Global oil price* or *Strait of Hormuz*.
2. **Story reveal + Explorer** â€” the default Explorer is an immersive Three.js globe with a compact companion causal rail. Opening a story begins a 5â€“8 second directed story reveal of the strongest evidence-backed main chain. The camera remains directed until completion; users can choose **Skip to explore** at any point. The full Explorer then supports rotate/zoom, branch selection, regional expansion, and filters.
3. **Evidence panel** â€” opens immediately on edge selection. It presents: plain-language mechanism; direction, strength, and lag; certainty; provenance; sources; and contested views where applicable. Paywalled sources remain visible with metadata, destination link, and a clear paywall label.

### Visual system

- **Tone:** cinematic and immersive, using charcoal as the base, amber as the primary active/evidence-supported signal, and red for disruption severity only.
- **Geography:** at global scale, countries use glowing pins; on zoom, the relevant country surface receives a subtle highlight. Geography answers *where does this land?*
- **Causal rail:** non-geographic conceptsâ€”such as oil price, freight cost, inflation, and food pressureâ€”live in the companion rail, not as floating globe nodes. The rail answers *what happens and why?*
- **Causal paths:** show one strongest main chain first. Other credible paths are selectable branches on the globe; selecting one changes the active rail and evidence panel.
- **High-density effects:** begin with expandable regional clusters. Selecting a cluster flies the camera to it and reveals its countries and effects.
- **Motion:** purposeful, brief particle flow and ripple pulses communicate activation and direction. The product is silent in v1. Motion never carries meaning by itself and must respect reduced-motion preferences.
- **Spatial semantics:** an arc may express causal hop or lag, never importance or certainty.

### Controls and navigation

- The causal rail is a compact overlay by default. Users can expand it for the full explanation or collapse it for an unobstructed globe.
- After the reveal, users can filter both globe and causal rail by consequence type, time lag, certainty, provenance, and severity.
- Default filters: all consequence types; immediate through months; established, emerging, and conditional pathways; curated and AI-suggested; all severities, with high-disruption effects visually prioritized.
- Users can return to their exact previous feed position with Back or open a persistent news-board drawer from the Explorer.
- First-time visitors receive a short 2â€“3 step onboarding: choose a story, watch the ripple, inspect the evidence. It can be revisited using a persistent Help button.

### Trust, accessibility, and scope

- Curated vs AI-suggested and certainty are always represented through explicit text labels and icons as well as color.
- If no established chain exists, source-grounded AI-suggested links may be shown as **emerging**. Unsupported links are never shown.
- Provide a text-based causal chain and keyboard-accessible equivalent for graph interactions. Never depend on color, sound, or motion alone.
- Provide an honest state when no supported ripple is available; do not manufacture a chain.
- v1 is desktop/WebGL-only. A 2D fallback, mobile Explorer, sharing selected paths, and event-to-event comparison are deferred.

**Deliverable before heavy build:** a clickable low-fi wireframe that validates the dense feed, 5â€“8 second story reveal, Three.js globe/causal-rail Explorer, immediate evidence panel, and key empty states.

---

## 13. Evaluation plan (quality = credibility)

- **Faithfulness:** do AI-generated explanations match their cited sources? (LLM-as-judge; Priya's toolkit.)
- **Mapping accuracy:** does the Linker map stories to the right nodes? (hand-labeled sample.)
- **Curated-edge review:** every curated edge peer-checked against its citation.
- **Hallucination rate:** track and drive down; block edges below a confidence bar.
- **User comprehension:** do testers correctly understand a ripple after using it? (small usability test, like Priya's VR study.)

---

## 14. Non-functional requirements

- **Cost:** ~$0â€“25/mo; GDELT free; cache LLM calls.
- **Deployment:** Vercel hosts the frontend SPA; Render hosts FastAPI and background/scheduled ingestion. Configure the frontend only with the public API base URL; keep provider keys and ingestion credentials in Render environment variables.
- **Database:** Render Postgres is the production source of truth for nodes, edges, evidence, stories, mappings, and cached ripple subgraphs. Use version-controlled JSON as the curated-graph authoring/import format and enable `pgvector` when embeddings are introduced.
- **Performance:** feed loads < 2s; ripple expansion < 1s (precompute/cache popular subgraphs); maintain a responsive desktop/WebGL story reveal and Explorer.
- **Freshness:** news within ~15â€“60 min of publication.
- **Legal:** snippet + link-out only; attribute bias data; open-source the mechanism graph + engine for transparency.
- **Privacy:** v1 has no user accounts or user data. Gemini free-tier calls are limited to public news/evidence excerpts; retain only the structured result and required citation metadata.
- **Accessibility:** keyboard-navigable graph, text causal-chain equivalent, reduced-motion support, alt text, and a color-blind-safe certainty palette. Color, motion, and sound never carry meaning alone.

---

## 15. Risks & mitigations

| Risk | Mitigation |
|---|---|
| LLM invents plausible-but-wrong links | Curated backbone + `ai_suggested` labeling + faithfulness eval + block low-confidence |
| GDELT firehose overwhelms | Filter hard by theme/country/date; one domain in v1 |
| Stories don't map cleanly to graph | Show "no established ripples yet" honestly; don't force chains |
| Overclaiming causation | Explicit correlation/causation/theory labels; strength + certainty |
| Scope creep (back to "everything") | This doc; narrow-but-deep discipline; v1 = energy only |
| Copyright | Snippet + link-out; no full republication |

---

## 16. Roadmap (phased)

**Phase 0 â€” Validate the two-layer idea (Week 1, "the spike"):**
- GDELT pull script for today's energy headlines (themes/entities).
- ~10 curated energy cause-effect links (JSON, sourced).
- Mapper: one live headline â†’ graph node â†’ printed ripple chain with sources. *No UI.*

**Phase 1 â€” Backend core (Weeks 2â€“3):**
- Node/edge schema finalized; ~30â€“50 curated edges; Render Postgres schema/migrations and JSON graph import in place.
- FastAPI endpoints (`/feed`, `/story`, `/ripples`, `/edge`).
- Linker + traversal working end-to-end (JSON output).

**Phase 2 â€” Frontend MVP (Weeks 4â€“5):**
- Dense live-news board + Three.js story reveal/Explorer + compact causal rail + immediate evidence panel. Ugly-but-real.

**Phase 3 â€” AI extension + trust (Week 5â€“6):**
- LLM gap-filling (grounded, labeled); certainty/provenance UI; source/bias chips.

**Phase 4 â€” Evaluation (Week 6):**
- Faithfulness + mapping-accuracy harness; fix top failure modes.

**Phase 5 â€” Ship & learn (Weeks 7â€“8):**
- Deploy to free hosting; put in front of real users; iterate; grow the graph.

**Later:** more domains; prediction layer; institutional features.

---

## 17. Proposed repo structure

```
ripple/
â”œâ”€â”€ README.md                 # points to this plan
â”œâ”€â”€ docs/
â”‚   â””â”€â”€ master_build_plan.md  # THIS document (ground truth)
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ graph/                # curated nodes + edges (JSON, source-controlled)
â”‚   â””â”€â”€ bias_ratings/         # attributed outlet bias data
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ ingest/               # GDELT pull + normalize
â”‚   â”œâ”€â”€ linker/               # story â†’ node mapping
â”‚   â”œâ”€â”€ graph/                # store + traversal
â”‚   â”œâ”€â”€ reasoning/            # LangGraph: decomposition, link-gen, explanation
â”‚   â”œâ”€â”€ retrieval/            # BM25 + embeddings
â”‚   â”œâ”€â”€ eval/                 # faithfulness + mapping harness
â”‚   â””â”€â”€ api/                  # FastAPI app
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ src/components/       # feed, graph, evidence panel
â”‚   â””â”€â”€ ...
â””â”€â”€ scripts/                  # week-1 spike scripts
```

---

## 18. Open decisions (to resolve as we go)

1. **First country focus for the feed** (or global energy feed?) â€” recommend global-energy to prove cross-border ripples.
2. **How curated edges get authored/reviewed** â€” solo now; consider a lightweight contribution format later.

---

## 19. Recommended next step

**Do Phase 0 â€” the spike â€” next.** It's the smallest thing that de-risks the single biggest unknown: *can we reliably map a fresh headline onto a stable mechanism graph and produce a sourced ripple chain?* Everything else (UI, scale, more domains) is easier and lower-risk than this. Concretely, the next deliverable is:

1. `scripts/pull_gdelt_energy.py` â€” fetch today's energy headlines + their GKG tags.
2. `data/graph/energy_v0.json` â€” ~10 hand-curated, sourced cause-effect edges.
3. `scripts/ripple_from_headline.py` â€” take one real headline, map it to a node, print the ripple chain with sources and certainty.

If that works and feels compelling in a terminal, the product is real and we build outward. If mapping is hard, we learn it now â€” for almost no cost.

*Parallel track:* validate the Section 12 experience with a clickable low-fi wireframe of the dense feed, guided story reveal, globe/causal-rail Explorer, and evidence states while the backend spike runs.

---

## Changelog
- **v1.1 (Jul 2026):** Integrated the Design/UX v1 decisions: desktop Three.js globe, guided story reveal, causal rail, visual system, filters, dense news board, evidence behavior, onboarding, and accessibility/trust constraints. Locked deployment to Vercel (frontend) + Render (FastAPI, scheduled jobs, and Postgres); Render Postgres is the v1 production source of truth. Added the causal-publication policy: default conditional pathways, 2â€“3 independent-source thresholds, and rule-derived certainty. Selected Gemini 3.5 Flash free tier for public-evidence-only v1 enrichment.
- **v1.0 (Jul 2026):** Initial ground-truth consolidation of vision, scope, architecture, data model, stack, AI/trust layers, design, eval, roadmap, repo structure.
