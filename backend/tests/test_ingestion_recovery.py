from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.main import app
from app.models import EventClaimResolution, IngestionRun, Story, StoryNodeMatch
from app.services.ingest.gdelt import GdeltProvider, RecordedGdeltDocClient
from app.services.ingest.gdelt_wiring import load_graph_link_context
from app.services.ingest.job import run_ingestion
from app.services.ingest.provider import NormalizedStory

ROOT = Path(__file__).resolve().parents[2]
RECORDED = ROOT / "data" / "fixtures" / "gdelt_doc_api_sample.json"
RUN_KEYS = ("test-m3-recovery", "test-m3-feed")


def _cleanup() -> None:
    with Session(get_engine()) as session, session.begin():
        live = [
            row
            for row in session.scalars(select(Story)).all()
            if row.slug.startswith("story.gdelt.") or row.slug.startswith("story.live.")
        ]
        for story in live:
            session.delete(story)
        session.execute(delete(IngestionRun).where(IngestionRun.run_key.in_(RUN_KEYS)))


@pytest.fixture(autouse=True)
def clean() -> Iterator[None]:
    _cleanup()
    yield
    _cleanup()


class _FailingProvider:
    def fetch(self) -> list[NormalizedStory]:
        raise RuntimeError("simulated ingestion failure")


def _live_story(slug: str, mapped_node: str | None) -> NormalizedStory:
    return NormalizedStory(
        slug=slug,
        headline="Live: energy ministers weigh supply options",
        published_at=datetime(2026, 7, 11, 12, 0, tzinfo=UTC),
        origin_location="Test Region",
        themes=["ECON_OILPRICE"],
        entities=[],
        source_outlet="test.invalid",
        source_url=HttpUrl("https://test.invalid/live-story"),
        source_excerpt="Live: energy ministers weigh supply options",
        event_status="threat_only",
        condition_met=False,
        prominence_reasons=["live GDELT ingestion", "published today"],
        fixture=False,
        mapped_node=mapped_node,
    )


class _OneShotProvider:
    def __init__(self, story: NormalizedStory) -> None:
        self._story = story

    def fetch(self) -> list[NormalizedStory]:
        return [self._story]


def test_failed_run_is_recorded_then_recovers() -> None:
    run_key = "test-m3-recovery"

    with Session(get_engine()) as session:
        with pytest.raises(RuntimeError, match="simulated ingestion failure"):
            run_ingestion(session, _FailingProvider(), run_key)

    with Session(get_engine()) as session:
        failed = session.scalar(select(IngestionRun).where(IngestionRun.run_key == run_key))
        assert failed is not None
        assert failed.status == "failed"
        assert "simulated ingestion failure" in (failed.error_message or "")

    story = _live_story("story.live.recovery", "commodity.oil_price")
    with Session(get_engine()) as session:
        result = run_ingestion(session, _OneShotProvider(story), run_key)
    assert result.status == "succeeded"

    with Session(get_engine()) as session:
        recovered = session.scalar(select(IngestionRun).where(IngestionRun.run_key == run_key))
        assert recovered is not None
        assert recovered.status == "succeeded"
        assert recovered.error_message is None
        persisted = session.scalar(select(Story).where(Story.slug == "story.live.recovery"))
        assert persisted is not None
        assert persisted.fixture is False


def test_unmatched_story_is_stored_without_a_manufactured_chain() -> None:
    story = _live_story("story.live.recovery", mapped_node=None)
    with Session(get_engine()) as session:
        run_ingestion(session, _OneShotProvider(story), "test-m3-feed")

    with Session(get_engine()) as session:
        persisted = session.scalar(select(Story).where(Story.slug == "story.live.recovery"))
        assert persisted is not None
        matches = session.scalars(
            select(StoryNodeMatch).where(StoryNodeMatch.story_id == persisted.id)
        ).all()
        resolutions = session.scalars(
            select(EventClaimResolution).where(EventClaimResolution.story_id == persisted.id)
        ).all()
        assert matches == []
        assert resolutions == []


def test_live_feed_serves_and_caches_conditional_ripple() -> None:
    with Session(get_engine()) as session:
        context = load_graph_link_context(session)
        provider = GdeltProvider(
            RecordedGdeltDocClient(RECORDED),
            context.index,
            context.themes,
            context.edge_counts,
            now=datetime(2026, 7, 11, 12, 0, tzinfo=UTC),
        )
        run_ingestion(session, provider, "test-m3-feed")

    with TestClient(app) as client:
        feed = client.get("/feed", params={"domain": "energy", "limit": 50}).json()
        live = [item for item in feed["items"] if item["story_id"].startswith("story.gdelt.")]
        assert live, "expected live GDELT stories in the feed"
        assert all(item["fixture"] is False for item in live)

        story_id = live[0]["story_id"]
        first = client.get(f"/story/{story_id}/ripples").json()
        second = client.get(f"/story/{story_id}/ripples").json()
        assert first["fixture"] is False
        assert first["edges"], "live story should traverse a curated ripple"
        assert all(edge["condition_met"] is False for edge in first["edges"])
        assert all(edge["claim_state"] == "conditional_pathway" for edge in first["edges"])
        assert first["cached"] is False
        assert second["cached"] is True
