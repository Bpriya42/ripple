"""Minimal, dependency-free ``.env`` loader for local development.

Values already present in the environment always win, so production hosts that
inject real environment variables (e.g. Render) are never overridden, and secrets
are never written anywhere. Lines are ``KEY=value``; ``#`` comments and blanks are
ignored.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)
