# Architecture

Ripple separates a volatile news layer from a stable, version-controlled
mechanism graph imported into PostgreSQL. Milestone 1 exposes a deterministic
FastAPI backend over PostgreSQL repositories. Story ripple composition joins
story-to-node matches, bounded graph traversal, event-specific resolutions, and
curated evidence before applying the publication gate. Responses are cached in
PostgreSQL with versioned keys and expiration.

The scheduled-ingestion boundary accepts a provider interface. Milestone 1
ships only a finite, checked-in GDELT-shaped fixture provider; live network
ingestion remains deferred. Frontend screens and LLM enrichment also remain
outside this milestone.
