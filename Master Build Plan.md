# Ripple — Master Build Plan (Ground Truth v1.0)

*Owner: Priya Balakrishnan · Last updated: July 2026*

> **Purpose of this document.** This is the single source of truth for the Ripple project. Every other file, skill, tool, or spec is built off the information here. When something changes, change it here first, then propagate. If two documents disagree, this one wins.

---

## 0. How to use this document

- **Sections 1–4** = what we're building and why (stable; changes rarely).
- **Sections 5–12** = how it works: experience, architecture, data, stack, AI, trust, design (the buildable core).
- **Sections 13–16** = quality, risk, roadmap.
- **Sections 17–19** = repo structure, open decisions, next steps.
- Keep a changelog at the bottom.

---

## 1. Product in one line

**Ripple is an explorable, near-real-time map of how the world is connected: click a news event, policy, country, or commodity and see how it ripples out to affect other places and things — at home and abroad — with the reasoning, evidence, and certainty behind every link.**

---

## 2. Problem & why now

People read a headline and rarely see the second- and third-order consequences — especially across borders (a strait closure → oil prices → inflation in importer nations → food stress). These ripple effects are **real and well-documented** by economists (monetary/policy spillovers, global value-chain contagion, chokepoint effects), but that knowledge is locked in academic papers, not accessible to ordinary readers.

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

**Ripple's one-sentence differentiation:** *Ground News maps coverage; Ripple maps consequences* — turning established cross-border cause-effect knowledge into something an ordinary person can explore.

---

## 4. Product definition & scope

- **Type (v1):** purely **informational / educational**. Shows *how things affect things*. **No prediction claims in v1** (prediction is a possible later layer).
- **Primary user (v1):** curious public, students, advocates, journalists. Designed so an NGO/gov/researcher can grow into it later.
- **Job-to-be-done:** *"I read this news — help me understand what it actually affects, and why, with evidence I can trust."*
- **North-star feel:** *"I had no idea that affects this — and now I understand why."*

**In scope (v1):** fresh news feed (one domain), clickable stories, home-ring + global-ring ripple map, evidence/certainty panel per link, hybrid curated+LLM knowledge.

**Out of scope (v1):** prediction/forecasting, all domains at once, full bias analytics, user accounts, mobile app, institutional dashboards.

---

## 5. Core experience & user flows

### Primary flow
1. **Browse** — a feed of fresh headlines (GDELT-fed, ~15-min fresh), filtered to the v1 domain, optionally with source/bias context (Ground News-style chips).
2. **Pick a story** — e.g. *"Iran threatens to close the Strait of Hormuz."*
3. **See the ripples** — a short, guided 5–8 second cinematic story reveal introduces the strongest evidence-backed causal chain. A Three.js globe shows where effects land; a companion causal rail states what happens and why. The user can always choose **Skip to explore**.
   - At world scale, affected countries appear as glowing pins; when zoomed in, the affected country surface is subtly highlighted.
   - When many countries are affected, effects begin as expandable regional clusters; selecting a region flies the camera to it and reveals country-level effects.
   - After the reveal, depth is user-controlled (expand one hop at a time) and credible alternative paths appear as selectable globe branches.
4. **Click a link (edge)** — panel shows: plain-language **mechanism (why)**, **direction**, **strength**, **lag**, **evidence/sources**, **certainty** (established / emerging / speculative), and whether it's **curated** or **AI-suggested**.
5. **Wander** — follow chains node to node; jump to any node via search (free exploration).

### Secondary flows
- Start from a **node** (e.g. "oil price") instead of a story and see what affects it / what it affects.
- **Share** a specific ripple view (URL encodes the node + expansion state).

---

## 6. System architecture

### The core insight: two layers linked
Separate what changes **fast** from what changes **slowly**.

- **Layer A — Fast news stream (volatile):** ingest fresh, entity-tagged news. Never hand-curated. Source: GDELT.
- **Layer B — Slow mechanism graph (stable):** curated + LLM-extended cause-effect relationships ("how the world works"). Maintained slowly; the trust backbone.
- **The Linker:** map a fresh story onto graph nodes (via its themes/entities/locations), then **traverse** the graph to produce the ripple map. RAG grounds every explanation in real text.

### Component diagram (logical)
```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND (React/TS)                   │
│   Headline feed  │  Ripple graph view  │  Evidence panel      │
└───────────────▲───────────────▲──────────────▲───────────────┘
                │ REST/JSON      │              │
┌───────────────┴───────────────┴──────────────┴───────────────┐
│                         BACKEND API (FastAPI)                 │
│  /feed   /story/{id}   /ripples/{node}   /edge/{id}           │
└───┬───────────────┬──────────────────┬──────────────┬────────┘
    │               │                  │              │
┌───▼───┐   ┌───────▼────────┐  ┌──────▼───────┐  ┌───▼─────────┐
│ NEWS  │   │  LINKER /       │  │ MECHANISM    │  │ REASONING   │
│ INGEST│   │  ENTITY MAPPER  │  │ GRAPH STORE  │  │ (LLM layer) │
│(GDELT)│──▶│ story→nodes     │─▶│ nodes+edges  │◀─│ RAG, decomp,│
└───────┘   │ (GKG tags+embed)│  │ (JSON/SQLite │  │ link-gen,   │
            └─────────────────┘  │  →Neo4j)     │  │ explanation │
                                 └──────┬───────┘  └───┬─────────┘
                                        │              │
                                 ┌──────▼──────────────▼───────┐
                                 │  EVIDENCE / RETRIEVAL STORE  │
                                 │  article text + citations    │
                                 │  (BM25 + embeddings)         │
                                 └──────────────────────────────┘
```

**Implementation note:** the diagram's mechanism-graph label reflects the early evolution. For v1 production, the graph store is Render Postgres; version-controlled JSON is used only for curated-graph authoring/import.

### Data flow (a story click)
`story_id → Linker maps to graph node(s) → traverse edges N hops → for each edge, attach curated evidence OR generate grounded link via LLM+RAG → return ripple subgraph (nodes+edges+evidence+certainty) → frontend renders map → user clicks edge → evidence panel`

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
  "mechanism": "≈30% of seaborne oil transits Hormuz; a supply threat raises crude prices.",
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
| Mechanism graph store | Versioned JSON → **Render Postgres** | JSON supports Phase 0 authoring/import; managed Postgres is the v1 production source of truth |
| Entity/theme → node mapping | GDELT GKG tags + embedding similarity | Reuses tags; cheap |
| Retrieval | BM25 + embeddings (`pgvector` in Render Postgres) | Priya's CIIR/RAG stack, re-pointed; keep relational data and embeddings together in v1 |
| Reasoning / orchestration | **LangGraph** (query decomposition, link-gen, explanation) | Priya already knows it |
| LLM | **Gemini 3.5 Flash free tier** via the Gemini Interactions API, cached aggressively | Free hosted reasoning, thinking, and structured output for public-evidence-only enrichment |
| Backend | **FastAPI** (Python) | Priya's stack |
| Frontend | **React + TypeScript** | Priya's stack |
| Graph visualization | **Three.js / React Three Fiber** + companion causal rail | Cinematic, geographic 3D Explorer; readable causal explanation remains outside the globe |
| Charts (if needed) | Recharts / uPlot | Priya has uPlot experience |
| Frontend hosting | **Vercel** | Deploy the React/Vite SPA globally with preview deployments |
| Backend + workers | **Render** | Host FastAPI and scheduled GDELT ingestion/cache-refresh jobs |
| **Est. running cost** | **~$0–25/month** | LLM calls only; GDELT free |

---

## 10. The AI / reasoning layer

Borrows the **method** from Hindsight (not its code): graph traversal + query decomposition + RAG + faithfulness evaluation, rebuilt for news.

1. **Story→node mapping (Linker):** GDELT tags + embeddings match a story to existing graph nodes; if none, create a candidate node.
2. **Traversal:** walk curated edges outward N hops to build the ripple subgraph.
3. **Event applicability:** for each candidate edge, extract only attributable story facts; compare them with the edge's required conditions; and classify the result as observed, established, emerging, conditional, or not shown.
4. **Gap-filling (LLM):** where the graph lacks an edge the story implies, the LLM proposes a **grounded** candidate edge (RAG over article + evidence), tagged `ai_suggested`. Human can later promote to `curated`.
5. **Evidence rules:** derive certainty and publication eligibility from rule-based evidence criteria, including source independence, directness, recency, contradiction, and impact severity. Require at least two independent sources for ordinary AI-suggested claims and three for high-impact/disruptive claims; a credible contradiction marks the link contested or suppresses it.
6. **Explanation:** LLM writes the plain-language "why" and explains the rule-derived status strictly from approved, cited evidence — **never invents numbers or claims without a source.**
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
- **Correlation ≠ causation shown explicitly** (edge `type`: study / historical / theory).
- **Strength + lag**, not just yes/no ("strongly, within weeks" vs "weakly, over years").
- **Contested links shown as contested**, with both views.
- **Copyright:** headlines + short snippets + link out (Ground News model); never republish full articles.

Relevant to Priya's background: BlueDot AI-safety cert + Responsible/Trustworthy AI coursework = applied trustworthy-AI design.

---

## 12. Design / UX plan

### Design north star

**Ripple is an explanation tool first and a graph tool second.** Its visual system makes cross-border consequences tangible while keeping every claim readable, sourced, and clearly qualified.

### Screens (v1)

1. **Live news board** — a dense, fast-scanning global-energy board. Story prominence is a transparent blend of recency, estimated global impact, and the richness/quality of available ripple evidence. Cards show headline, time, place, source context, and compact explanations such as *recent*, *high cross-border impact*, and *strong ripple evidence*. The feed contains no animated globe previews. If fresh relevant news is unavailable, it offers curated concept entry points such as *Global oil price* or *Strait of Hormuz*.
2. **Story reveal + Explorer** — the default Explorer is an immersive Three.js globe with a compact companion causal rail. Opening a story begins a 5–8 second directed story reveal of the strongest evidence-backed main chain. The camera remains directed until completion; users can choose **Skip to explore** at any point. The full Explorer then supports rotate/zoom, branch selection, regional expansion, and filters.
3. **Evidence panel** — opens immediately on edge selection. It presents: plain-language mechanism; direction, strength, and lag; certainty; provenance; sources; and contested views where applicable. Paywalled sources remain visible with metadata, destination link, and a clear paywall label.

### Visual system

- **Tone:** cinematic and immersive, using charcoal as the base, amber as the primary active/evidence-supported signal, and red for disruption severity only.
- **Geography:** at global scale, countries use glowing pins; on zoom, the relevant country surface receives a subtle highlight. Geography answers *where does this land?*
- **Causal rail:** non-geographic concepts—such as oil price, freight cost, inflation, and food pressure—live in the companion rail, not as floating globe nodes. The rail answers *what happens and why?*
- **Causal paths:** show one strongest main chain first. Other credible paths are selectable branches on the globe; selecting one changes the active rail and evidence panel.
- **High-density effects:** begin with expandable regional clusters. Selecting a cluster flies the camera to it and reveals its countries and effects.
- **Motion:** purposeful, brief particle flow and ripple pulses communicate activation and direction. The product is silent in v1. Motion never carries meaning by itself and must respect reduced-motion preferences.
- **Spatial semantics:** an arc may express causal hop or lag, never importance or certainty.

### Controls and navigation

- The causal rail is a compact overlay by default. Users can expand it for the full explanation or collapse it for an unobstructed globe.
- After the reveal, users can filter both globe and causal rail by consequence type, time lag, certainty, provenance, and severity.
- Default filters: all consequence types; immediate through months; established, emerging, and conditional pathways; curated and AI-suggested; all severities, with high-disruption effects visually prioritized.
- Users can return to their exact previous feed position with Back or open a persistent news-board drawer from the Explorer.
- First-time visitors receive a short 2–3 step onboarding: choose a story, watch the ripple, inspect the evidence. It can be revisited using a persistent Help button.

### Trust, accessibility, and scope

- Curated vs AI-suggested and certainty are always represented through explicit text labels and icons as well as color.
- If no established chain exists, source-grounded AI-suggested links may be shown as **emerging**. Unsupported links are never shown.
- Provide a text-based causal chain and keyboard-accessible equivalent for graph interactions. Never depend on color, sound, or motion alone.
- Provide an honest state when no supported ripple is available; do not manufacture a chain.
- v1 is desktop/WebGL-only. A 2D fallback, mobile Explorer, sharing selected paths, and event-to-event comparison are deferred.

**Deliverable before heavy build:** a clickable low-fi wireframe that validates the dense feed, 5–8 second story reveal, Three.js globe/causal-rail Explorer, immediate evidence panel, and key empty states.

---

## 13. Evaluation plan (quality = credibility)

- **Faithfulness:** do AI-generated explanations match their cited sources? (LLM-as-judge; Priya's toolkit.)
- **Mapping accuracy:** does the Linker map stories to the right nodes? (hand-labeled sample.)
- **Curated-edge review:** every curated edge peer-checked against its citation.
- **Hallucination rate:** track and drive down; block edges below a confidence bar.
- **User comprehension:** do testers correctly understand a ripple after using it? (small usability test, like Priya's VR study.)

---

## 14. Non-functional requirements

- **Cost:** ~$0–25/mo; GDELT free; cache LLM calls.
- **Deployment:** Vercel hosts the frontend SPA; Render hosts FastAPI and background/scheduled ingestion. Configure the frontend only with the public API base URL; keep provider keys and ingestion credentials in Render environment variables.
- **Database:** Render Postgres is the production source of truth for nodes, edges, evidence, stories, mappings, and cached ripple subgraphs. Use version-controlled JSON as the curated-graph authoring/import format and enable `pgvector` when embeddings are introduced.
- **Performance:** feed loads < 2s; ripple expansion < 1s (precompute/cache popular subgraphs); maintain a responsive desktop/WebGL story reveal and Explorer.
- **Freshness:** news within ~15–60 min of publication.
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

**Phase 0 — Validate the two-layer idea (Week 1, "the spike"):**
- GDELT pull script for today's energy headlines (themes/entities).
- ~10 curated energy cause-effect links (JSON, sourced).
- Mapper: one live headline → graph node → printed ripple chain with sources. *No UI.*

**Phase 1 — Backend core (Weeks 2–3):**
- Node/edge schema finalized; ~30–50 curated edges; Render Postgres schema/migrations and JSON graph import in place.
- FastAPI endpoints (`/feed`, `/story`, `/ripples`, `/edge`).
- Linker + traversal working end-to-end (JSON output).

**Phase 2 — Frontend MVP (Weeks 4–5):**
- Dense live-news board + Three.js story reveal/Explorer + compact causal rail + immediate evidence panel. Ugly-but-real.

**Phase 3 — AI extension + trust (Week 5–6):**
- LLM gap-filling (grounded, labeled); certainty/provenance UI; source/bias chips.

**Phase 4 — Evaluation (Week 6):**
- Faithfulness + mapping-accuracy harness; fix top failure modes.

**Phase 5 — Ship & learn (Weeks 7–8):**
- Deploy to free hosting; put in front of real users; iterate; grow the graph.

**Later:** more domains; prediction layer; institutional features.

---

## 17. Proposed repo structure

```
ripple/
├── README.md                 # points to this plan
├── docs/
│   └── master_build_plan.md  # THIS document (ground truth)
├── data/
│   ├── graph/                # curated nodes + edges (JSON, source-controlled)
│   └── bias_ratings/         # attributed outlet bias data
├── backend/
│   ├── ingest/               # GDELT pull + normalize
│   ├── linker/               # story → node mapping
│   ├── graph/                # store + traversal
│   ├── reasoning/            # LangGraph: decomposition, link-gen, explanation
│   ├── retrieval/            # BM25 + embeddings
│   ├── eval/                 # faithfulness + mapping harness
│   └── api/                  # FastAPI app
├── frontend/
│   ├── src/components/       # feed, graph, evidence panel
│   └── ...
└── scripts/                  # week-1 spike scripts
```

---

## 18. Open decisions (to resolve as we go)

1. **First country focus for the feed** (or global energy feed?) — recommend global-energy to prove cross-border ripples.
2. **How curated edges get authored/reviewed** — solo now; consider a lightweight contribution format later.

---

## 19. Recommended next step

**Do Phase 0 — the spike — next.** It's the smallest thing that de-risks the single biggest unknown: *can we reliably map a fresh headline onto a stable mechanism graph and produce a sourced ripple chain?* Everything else (UI, scale, more domains) is easier and lower-risk than this. Concretely, the next deliverable is:

1. `scripts/pull_gdelt_energy.py` — fetch today's energy headlines + their GKG tags.
2. `data/graph/energy_v0.json` — ~10 hand-curated, sourced cause-effect edges.
3. `scripts/ripple_from_headline.py` — take one real headline, map it to a node, print the ripple chain with sources and certainty.

If that works and feels compelling in a terminal, the product is real and we build outward. If mapping is hard, we learn it now — for almost no cost.

*Parallel track:* validate the Section 12 experience with a clickable low-fi wireframe of the dense feed, guided story reveal, globe/causal-rail Explorer, and evidence states while the backend spike runs.

---

## Changelog
- **v1.1 (Jul 2026):** Integrated the Design/UX v1 decisions: desktop Three.js globe, guided story reveal, causal rail, visual system, filters, dense news board, evidence behavior, onboarding, and accessibility/trust constraints. Locked deployment to Vercel (frontend) + Render (FastAPI, scheduled jobs, and Postgres); Render Postgres is the v1 production source of truth. Added the causal-publication policy: default conditional pathways, 2–3 independent-source thresholds, and rule-derived certainty. Selected Gemini 3.5 Flash free tier for public-evidence-only v1 enrichment.
- **v1.0 (Jul 2026):** Initial ground-truth consolidation of vision, scope, architecture, data model, stack, AI/trust layers, design, eval, roadmap, repo structure.
