# API contract

The generated contract is committed at `docs/openapi.json`. Public routes use
stable slugs; internal PostgreSQL UUIDs are never exposed as identifiers.

## Endpoints

- `GET /health` checks API and database availability.
- `GET /feed?domain=energy&limit=&cursor=` returns newest-first cursor pages.
- `GET /story/{story_id}` returns a story, sources, and mapped graph nodes.
- `GET /story/{story_id}/ripples?depth=` returns story-specific claim records.
- `GET /concept/{node_slug}/ripples?depth=` returns stable mechanisms without
  fabricating an event status.
- `GET /edge/{edge_id}` returns a stable mechanism and immediate evidence.

Traversal defaults to depth 2 and accepts depths 1 through 3. Invalid cursors
return `400`; invalid depth values return `422`; missing resources return `404`.

Every story-specific returned edge includes its story and event status,
required condition, condition result, deterministic claim state and certainty
reasons, provenance, high-impact classification, evidence, contested status,
and publication decision. The high-impact flag is curated graph metadata used
for deterministic disruption-severity presentation; it is not an event outcome.
`not_shown`, unpublished, and evidence-free causal edges are excluded.

All current feed records are explicitly marked fixtures. Source URLs under the
reserved `.invalid` domain identify fictional news fixtures; causal evidence
links point to the cited institutional sources in the curated graph.
