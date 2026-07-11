# Architecture

Ripple separates a volatile news layer from a stable, version-controlled
mechanism graph imported into PostgreSQL. Milestone 0 implements only the
deterministic graph, policy gate, fixture linker, bounded traversal, and CLI.
FastAPI, live ingestion, frontend screens, and LLM enrichment begin in later
milestones.
