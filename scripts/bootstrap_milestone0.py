from __future__ import annotations

import subprocess
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.db.session import build_engine
from import_graph import import_graph

ROOT = Path(__file__).resolve().parents[1]


def wait_for_database(attempts: int = 30) -> None:
    engine = build_engine()
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == attempts:
                raise
            time.sleep(1)


def main() -> None:
    subprocess.run(
        ["docker", "compose", "up", "-d", "--wait", "postgres"],
        cwd=ROOT,
        check=True,
    )
    wait_for_database()
    config = Config(str(ROOT / "backend" / "alembic.ini"))
    command.upgrade(config, "head")
    nodes, edges, sources = import_graph()
    print(
        "Milestone 0 database ready: "
        f"migration=head, fixture_nodes={nodes}, fixture_edges={edges}, fixture_sources={sources}"
    )


if __name__ == "__main__":
    main()
