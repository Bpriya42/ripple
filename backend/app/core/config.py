from __future__ import annotations

import os

DEFAULT_DATABASE_URL = "postgresql+psycopg://ripple:ripple@localhost:5432/ripple"
DEFAULT_FRONTEND_ORIGIN = "http://localhost:5173"
DEFAULT_GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_LLM_PROVIDER = "disabled"
DEFAULT_LLM_MODEL = "gemini-3.5-flash"
DEFAULT_LLM_BASE_URL = "https://generativelanguage.googleapis.com"


def database_url() -> str:
    """Return the configured database URL without loading or logging secrets.

    Managed hosts (e.g. Render) hand out a bare ``postgresql://`` URL, which
    SQLAlchemy would route to the uninstalled psycopg2 driver. Normalize it to
    the psycopg 3 driver this project depends on.
    """
    url = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    elif url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    return url


def frontend_origins() -> list[str]:
    """Return the allowed browser origins for CORS.

    ``FRONTEND_ORIGIN`` may hold a single origin or a comma-separated list so a
    deployment can serve the same API to a production and a preview frontend.
    """
    raw = os.getenv("FRONTEND_ORIGIN") or DEFAULT_FRONTEND_ORIGIN
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def gdelt_base_url() -> str:
    """Return the GDELT 2.0 DOC API base URL used by the live ingestion path."""
    return os.getenv("GDELT_BASE_URL") or DEFAULT_GDELT_BASE_URL


def llm_provider() -> str:
    """Return the configured LLM provider.

    Defaults to ``disabled`` so the deterministic product runs with no model
    calls. Set ``LLM_PROVIDER=gemini`` (and ``LLM_API_KEY``) to enable
    enrichment. Enrichment is always additive and never a prerequisite.
    """
    return (os.getenv("LLM_PROVIDER") or DEFAULT_LLM_PROVIDER).strip().lower()


def llm_model() -> str:
    """Return the configured LLM model id."""
    return os.getenv("LLM_MODEL") or DEFAULT_LLM_MODEL


def llm_base_url() -> str:
    """Return the base URL for the Generative Language API."""
    return os.getenv("LLM_BASE_URL") or DEFAULT_LLM_BASE_URL


def llm_api_key() -> str | None:
    """Return the LLM API key from the environment, or None if unset.

    The value is never logged or echoed. Absence disables live model calls.
    """
    key = os.getenv("LLM_API_KEY")
    return key or None
