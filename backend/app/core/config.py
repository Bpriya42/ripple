from __future__ import annotations

import os

DEFAULT_DATABASE_URL = "postgresql+psycopg://ripple:ripple@localhost:5432/ripple"


def database_url() -> str:
    """Return the configured database URL without loading or logging secrets."""
    return os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
