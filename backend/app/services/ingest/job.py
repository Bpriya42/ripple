from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import (
    Edge,
    EventClaimResolution,
    IngestionRun,
    Node,
    Story,
    StoryNodeMatch,
    StorySource,
)
from app.schemas.graph import Provenance
from app.services.ingest.provider import NormalizedStory, StoryProvider
from app.services.publication_policy import PolicyInput, evaluate_publication


@dataclass(frozen=True)
class IngestionResult:
    run_key: str
    status: str
    records_seen: int
    already_processed: bool


def run_ingestion(session: Session, provider: StoryProvider, run_key: str) -> IngestionResult:
    """Run one idempotent ingestion pass, owning its own transactions.

    The run ledger is committed separately from the ingested data so a failure
    is durably recorded as ``failed`` (with the partial data rolled back) and a
    later run with the same key can recover. Pass a plain ``Session`` that is not
    already inside a ``begin()`` block.
    """
    existing = session.scalar(select(IngestionRun).where(IngestionRun.run_key == run_key))
    if existing is not None and existing.status == "succeeded":
        return IngestionResult(run_key, existing.status, existing.records_seen, True)

    now = datetime.now(UTC)
    if existing is None:
        run = IngestionRun(run_key=run_key, status="running", started_at=now)
        session.add(run)
    else:
        run = existing
        run.status = "running"
        run.started_at = now
        run.completed_at = None
        run.error_message = None
    session.commit()  # persist the run marker independently of the ingested data

    try:
        records = provider.fetch()
        for record in records:
            _persist_record(session, record)
        succeeded = session.scalar(select(IngestionRun).where(IngestionRun.run_key == run_key))
        assert succeeded is not None
        succeeded.status = "succeeded"
        succeeded.records_seen = len(records)
        succeeded.completed_at = datetime.now(UTC)
        session.commit()
        return IngestionResult(run_key, succeeded.status, len(records), False)
    except Exception as exc:
        session.rollback()  # discard partial data; the committed run marker survives
        failed = session.scalar(select(IngestionRun).where(IngestionRun.run_key == run_key))
        assert failed is not None
        failed.status = "failed"
        failed.error_message = str(exc)
        failed.completed_at = datetime.now(UTC)
        session.commit()
        raise


def _persist_record(session: Session, record: NormalizedStory) -> None:
    node = None
    if record.mapped_node is not None:
        node = session.scalar(select(Node).where(Node.slug == record.mapped_node))
        if node is None:
            raise ValueError(f"unknown mapped node: {record.mapped_node}")
    match_method = "fixture_mock_gdelt" if record.fixture else "gdelt_theme"

    session.execute(
        insert(Story)
        .values(
            slug=record.slug,
            headline=record.headline,
            domain="energy",
            event_status=record.event_status,
            origin_location=record.origin_location,
            prominence_reasons=record.prominence_reasons,
            themes=record.themes,
            entities=record.entities,
            published_at=record.published_at,
            fixture=record.fixture,
        )
        .on_conflict_do_update(
            index_elements=[Story.slug],
            set_={
                "headline": record.headline,
                "event_status": record.event_status,
                "origin_location": record.origin_location,
                "prominence_reasons": record.prominence_reasons,
                "themes": record.themes,
                "entities": record.entities,
                "published_at": record.published_at,
                "fixture": record.fixture,
            },
        )
    )
    story = session.scalar(select(Story).where(Story.slug == record.slug))
    assert story is not None
    session.execute(delete(StorySource).where(StorySource.story_id == story.id))
    session.execute(delete(StoryNodeMatch).where(StoryNodeMatch.story_id == story.id))
    session.execute(delete(EventClaimResolution).where(EventClaimResolution.story_id == story.id))
    session.add(
        StorySource(
            story_id=story.id,
            outlet=record.source_outlet,
            url=str(record.source_url),
            excerpt=record.source_excerpt,
            independent_group=(
                f"fixture:{record.source_outlet}"
                if record.fixture
                else f"gdelt:{record.source_outlet}"
            ),
            paywalled=False,
        )
    )
    if node is None:
        # Honest empty ripple: the story is stored and shown in the feed, but no
        # chain is manufactured when no curated node matched.
        return
    session.add(
        StoryNodeMatch(
            story_id=story.id,
            node_id=node.id,
            match_method=match_method,
            score=1.0,
        )
    )
    for edge in session.scalars(select(Edge).where(Edge.from_node_id == node.id)).all():
        decision = evaluate_publication(
            PolicyInput(
                provenance=Provenance(edge.provenance),
                condition_met=record.condition_met,
                independent_source_count=1,
                high_impact=edge.high_impact,
                contradiction=edge.contested,
                contradiction_can_be_presented=bool(edge.contested_views),
            )
        )
        session.add(
            EventClaimResolution(
                story_id=story.id,
                edge_id=edge.id,
                event_status=record.event_status,
                required_condition=edge.required_condition,
                condition_met=record.condition_met,
                claim_state=decision.claim_state.value,
                certainty=decision.certainty.value,
                certainty_reasons=list(decision.certainty_reasons),
                publish=decision.publish,
                contested=decision.contested,
            )
        )
