"""Manual GDELT energy-headline spike (inspection only; never persists).

Fetches today's energy headlines per curated GDELT theme, maps each to a
curated graph node with the deterministic linker, and prints the result. Use
``--dry-run`` to replay the recorded DOC API fixture without any network access.

    uv run --project backend python scripts/pull_gdelt_energy.py --dry-run
    uv run --project backend python scripts/pull_gdelt_energy.py            # live
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.services.ingest.gdelt import (
    GdeltDocClient,
    GdeltProvider,
    HttpGdeltDocClient,
    RecordedGdeltDocClient,
)
from app.services.ingest.gdelt_wiring import load_graph_link_context

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDED_GDELT = ROOT / "data" / "fixtures" / "gdelt_doc_api_sample.json"


def pull(dry_run: bool, recorded: Path) -> list[dict[str, object]]:
    with Session(get_engine()) as session:
        context = load_graph_link_context(session)
    client: GdeltDocClient
    if dry_run:
        client = RecordedGdeltDocClient(recorded)
    else:
        client = HttpGdeltDocClient()
    provider = GdeltProvider(client, context.index, context.themes, context.edge_counts)
    stories = provider.fetch()
    return [
        {
            "headline": story.headline,
            "published_at": story.published_at.isoformat(),
            "origin": story.origin_location,
            "themes": story.themes,
            "mapped_node": story.mapped_node,
            "event_status": story.event_status,
            # Live ingestion never asserts an outcome occurred.
            "condition_met": story.condition_met,
        }
        for story in stories
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull and map today's energy headlines from GDELT"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Replay the recorded DOC API fixture instead of calling GDELT.",
    )
    parser.add_argument("--recorded", type=Path, default=DEFAULT_RECORDED_GDELT)
    args = parser.parse_args()

    rows = pull(args.dry_run, args.recorded)
    source = "recorded fixture" if args.dry_run else "live GDELT"
    print(
        f"# {len(rows)} energy headline(s) from {source}; condition_met is always False on ingest"
    )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
