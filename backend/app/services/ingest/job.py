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
from app.services.ingest.provider import StoryProvider
from app.services.publication_policy import PolicyInput, evaluate_publication


@dataclass(frozen=True)
class IngestionResult:
    run_key: str
    status: str
    records_seen: int
    already_processed: bool


def run_ingestion(session: Session, provider: StoryProvider, run_key: str) -> IngestionResult:
    existing = session.scalar(select(IngestionRun).where(IngestionRun.run_key == run_key))
    if existing is not None and existing.status == "succeeded":
        return IngestionResult(run_key, existing.status, existing.records_seen, True)

    now = datetime.now(UTC)
    if existing is None:
        run = IngestionRun(run_key=run_key, status="running", started_at=now)
        session.add(run)
        session.flush()
    else:
        run = existing
        run.status = "running"
        run.started_at = now
        run.completed_at = None
        run.error_message = None

    try:
        records = provider.fetch()
        nodes = {node.slug: node for node in session.scalars(select(Node)).all()}
        for record in records:
            node = nodes.get(record.mapped_node)
            if node is None:
                raise ValueError(f"unknown mapped node: {record.mapped_node}")
            session.execute(
                insert(Story)
                .values(
                    slug=record.slug,
                    headline=record.headline,
                    domain="energy",
                    event_status=record.event_status,
                    origin_location=record.origin_location,
                    prominence_reasons=["fixture", "mocked scheduled ingestion"],
                    themes=record.themes,
                    entities=record.entities,
                    published_at=record.published_at,
                    fixture=True,
                )
                .on_conflict_do_update(
                    index_elements=[Story.slug],
                    set_={
                        "headline": record.headline,
                        "event_status": record.event_status,
                        "origin_location": record.origin_location,
                        "prominence_reasons": ["fixture", "mocked scheduled ingestion"],
                        "themes": record.themes,
                        "entities": record.entities,
                        "published_at": record.published_at,
                        "fixture": True,
                    },
                )
            )
            story = session.scalar(select(Story).where(Story.slug == record.slug))
            assert story is not None
            session.execute(delete(StorySource).where(StorySource.story_id == story.id))
            session.execute(delete(StoryNodeMatch).where(StoryNodeMatch.story_id == story.id))
            session.execute(
                delete(EventClaimResolution).where(EventClaimResolution.story_id == story.id)
            )
            session.add(
                StorySource(
                    story_id=story.id,
                    outlet=record.source_outlet,
                    url=str(record.source_url),
                    excerpt=record.source_excerpt,
                    independent_group=f"fixture:{record.source_outlet}",
                    paywalled=False,
                )
            )
            session.add(
                StoryNodeMatch(
                    story_id=story.id,
                    node_id=node.id,
                    match_method="fixture_mock_gdelt",
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
        run.status = "succeeded"
        run.records_seen = len(records)
        run.completed_at = datetime.now(UTC)
        session.flush()
        return IngestionResult(run_key, run.status, len(records), False)
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.completed_at = datetime.now(UTC)
        session.flush()
        raise
