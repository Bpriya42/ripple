from __future__ import annotations

import argparse
import logging
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
from app.services.ingest.job import run_ingestion
from app.services.ingest.provider import FixtureGdeltProvider, StoryProvider

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FIXTURE = ROOT / "data" / "fixtures" / "gdelt_energy_sample.json"

logger = logging.getLogger("ripple.ingest")


def _build_provider(session: Session, args: argparse.Namespace) -> StoryProvider:
    if args.provider == "fixture":
        return FixtureGdeltProvider(args.fixture)

    context = load_graph_link_context(session)
    client: GdeltDocClient
    if args.recorded is not None:
        client = RecordedGdeltDocClient(args.recorded)
    else:
        client = HttpGdeltDocClient()
    return GdeltProvider(client, context.index, context.themes, context.edge_counts)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Run the finite Ripple ingestion job. Live GDELT access is opt-in."
    )
    parser.add_argument("--provider", choices=("fixture", "gdelt"), default="fixture")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument(
        "--recorded",
        type=Path,
        default=None,
        help="Replay a recorded DOC API fixture instead of calling GDELT (with --provider gdelt).",
    )
    parser.add_argument("--run-key", default="fixture-gdelt-energy-sample-v1")
    args = parser.parse_args()

    logger.info("ingestion starting provider=%s run_key=%s", args.provider, args.run_key)
    with Session(get_engine()) as session:
        provider = _build_provider(session, args)
        result = run_ingestion(session, provider, args.run_key)
    logger.info(
        "ingestion %s run_key=%s records_seen=%d already_processed=%s",
        result.status,
        result.run_key,
        result.records_seen,
        result.already_processed,
    )
    print(
        f"Ingestion {result.status}: run_key={result.run_key}, "
        f"records_seen={result.records_seen}, already_processed={result.already_processed}"
    )


if __name__ == "__main__":
    main()
