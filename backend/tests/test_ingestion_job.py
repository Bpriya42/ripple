from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.models import IngestionRun, Story
from app.services.ingest.job import run_ingestion
from app.services.ingest.provider import FixtureGdeltProvider

ROOT = Path(__file__).resolve().parents[2]


def test_mocked_gdelt_ingestion_is_idempotent() -> None:
    run_key = "test-fixture-gdelt-idempotency"
    story_slug = "story.fixture.gdelt.mock-gas-threat"
    provider = FixtureGdeltProvider(ROOT / "data" / "fixtures" / "gdelt_energy_sample.json")
    with Session(get_engine()) as session, session.begin():
        session.execute(delete(IngestionRun).where(IngestionRun.run_key == run_key))
        story = session.scalar(select(Story).where(Story.slug == story_slug))
        if story is not None:
            session.delete(story)

    with Session(get_engine()) as session, session.begin():
        first = run_ingestion(session, provider, run_key)
    with Session(get_engine()) as session, session.begin():
        second = run_ingestion(session, provider, run_key)
        count = len(session.scalars(select(Story).where(Story.slug == story_slug)).all())

    assert first.status == "succeeded"
    assert first.records_seen == 1
    assert first.already_processed is False
    assert second.already_processed is True
    assert count == 1
