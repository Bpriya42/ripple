from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.services.ingest.job import run_ingestion
from app.services.ingest.provider import FixtureGdeltProvider

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FIXTURE = ROOT / "data" / "fixtures" / "gdelt_energy_sample.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the finite Ripple ingestion job (fixture provider in Milestone 1)"
    )
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--run-key", default="fixture-gdelt-energy-sample-v1")
    args = parser.parse_args()
    with Session(get_engine()) as session, session.begin():
        result = run_ingestion(session, FixtureGdeltProvider(args.fixture), args.run_key)
    print(
        f"Ingestion {result.status}: run_key={result.run_key}, "
        f"records_seen={result.records_seen}, already_processed={result.already_processed}"
    )


if __name__ == "__main__":
    main()
