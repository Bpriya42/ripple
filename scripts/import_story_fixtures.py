from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.session import build_engine
from app.models import (
    Edge,
    EventClaimResolution,
    Node,
    RippleCache,
    Story,
    StoryNodeMatch,
    StorySource,
)
from app.schemas.graph import Provenance
from app.services.fixtures import load_story_fixtures
from app.services.publication_policy import PolicyInput, evaluate_publication

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORIES = ROOT / "data" / "fixtures" / "stories.json"


def import_story_fixtures(path: Path = DEFAULT_STORIES) -> int:
    fixtures = load_story_fixtures(path)
    with Session(build_engine()) as session, session.begin():
        nodes = {node.slug: node for node in session.scalars(select(Node)).all()}
        if not nodes:
            raise RuntimeError("graph fixtures must be imported before story fixtures")

        for fixture in fixtures.values():
            if fixture.mapped_node not in nodes:
                raise ValueError(f"unknown mapped node: {fixture.mapped_node}")
            session.execute(
                insert(Story)
                .values(
                    slug=fixture.id,
                    headline=fixture.headline,
                    domain=fixture.domain,
                    event_status=fixture.event_status,
                    origin_location=fixture.origin_location,
                    prominence_reasons=fixture.prominence_reasons,
                    themes=fixture.themes,
                    entities=fixture.entities,
                    published_at=fixture.published_at,
                    fixture=True,
                )
                .on_conflict_do_update(
                    index_elements=[Story.slug],
                    set_={
                        "headline": fixture.headline,
                        "domain": fixture.domain,
                        "event_status": fixture.event_status,
                        "origin_location": fixture.origin_location,
                        "prominence_reasons": fixture.prominence_reasons,
                        "themes": fixture.themes,
                        "entities": fixture.entities,
                        "published_at": fixture.published_at,
                        "fixture": True,
                    },
                )
            )
            story = session.scalar(select(Story).where(Story.slug == fixture.id))
            assert story is not None
            session.execute(delete(StorySource).where(StorySource.story_id == story.id))
            session.execute(
                delete(StoryNodeMatch).where(StoryNodeMatch.story_id == story.id)
            )
            session.execute(
                delete(EventClaimResolution).where(
                    EventClaimResolution.story_id == story.id
                )
            )
            for source in fixture.sources:
                session.add(
                    StorySource(
                        story_id=story.id,
                        outlet=source.outlet,
                        url=str(source.url),
                        excerpt=source.excerpt,
                        independent_group=source.independent_group,
                        paywalled=source.paywalled,
                    )
                )
            node = nodes[fixture.mapped_node]
            session.add(
                StoryNodeMatch(
                    story_id=story.id,
                    node_id=node.id,
                    match_method="fixture_exact",
                    score=fixture.match_score,
                )
            )
            edges = session.scalars(
                select(Edge).where(Edge.from_node_id == node.id)
            ).all()
            for edge in edges:
                decision = evaluate_publication(
                    PolicyInput(
                        provenance=Provenance(edge.provenance),
                        condition_met=fixture.condition_met,
                        direct_outcome_evidence=fixture.direct_outcome_evidence,
                        independent_source_count=len(
                            {source.independent_group for source in fixture.sources}
                        ),
                        high_impact=edge.high_impact,
                        contradiction=edge.contested,
                        contradiction_can_be_presented=bool(edge.contested_views),
                    )
                )
                session.add(
                    EventClaimResolution(
                        story_id=story.id,
                        edge_id=edge.id,
                        event_status=fixture.event_status,
                        required_condition=edge.required_condition,
                        condition_met=fixture.condition_met,
                        claim_state=decision.claim_state.value,
                        certainty=decision.certainty.value,
                        certainty_reasons=list(decision.certainty_reasons),
                        publish=decision.publish,
                        contested=decision.contested,
                    )
                )
        session.execute(delete(RippleCache))
    return len(fixtures)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import explicitly marked story fixtures"
    )
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_STORIES)
    args = parser.parse_args()
    count = import_story_fixtures(args.path)
    print(f"Imported story fixtures: {count}")


if __name__ == "__main__":
    main()
