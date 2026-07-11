from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.schemas.graph import Provenance
from app.services.fixtures import load_story_fixture
from app.services.graph import bounded_traversal, load_graph
from app.services.publication_policy import PolicyInput, evaluate_publication

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "graph" / "energy_v0.json"
STORY_PATH = ROOT / "data" / "fixtures" / "stories.json"


def build_ripple(fixture_name: str, depth: int = 2) -> dict[str, object]:
    graph = load_graph(GRAPH_PATH)
    story = load_story_fixture(STORY_PATH, fixture_name)
    evidence = {source.id: source for source in graph.evidence_sources}
    chain: list[dict[str, object]] = []
    node_depths = {story.mapped_node: 0}
    for edge in bounded_traversal(graph, story.mapped_node, depth):
        hop = node_depths[edge.from_node] + 1
        node_depths[edge.to_node] = min(hop, node_depths.get(edge.to_node, hop))
        # Only the fixture's first mapped event can establish an event-specific
        # condition. Downstream mechanisms remain conditional in the spike.
        is_mapped_event_edge = edge.from_node == story.mapped_node
        condition_met = story.condition_met if is_mapped_event_edge else False
        direct_evidence = (
            story.direct_outcome_evidence if is_mapped_event_edge else False
        )
        decision = evaluate_publication(
            PolicyInput(
                provenance=Provenance(edge.provenance),
                condition_met=condition_met,
                direct_outcome_evidence=direct_evidence,
                independent_source_count=len(
                    {evidence[item].independent_group for item in edge.evidence_ids}
                ),
                high_impact=edge.high_impact,
                contradiction=edge.contested,
                contradiction_can_be_presented=bool(edge.contested_views),
            )
        )
        chain.append(
            {
                "hop": hop,
                "edge_id": edge.id,
                "from": edge.from_node,
                "to": edge.to_node,
                "event_status": story.event_status,
                "required_condition": edge.required_condition,
                "condition_met": condition_met,
                "claim_state": decision.claim_state.value,
                "certainty": decision.certainty.value,
                "certainty_reasons": list(decision.certainty_reasons),
                "provenance": edge.provenance.value,
                "publish": decision.publish,
                "contested": decision.contested,
                "mechanism": edge.mechanism,
                "evidence": [
                    {
                        "title": evidence[source_id].title,
                        "publisher": evidence[source_id].publisher,
                        "url": str(evidence[source_id].url),
                    }
                    for source_id in edge.evidence_ids
                ],
            }
        )
    return {
        "fixture": True,
        "story_id": story.id,
        "headline": story.headline,
        "mapped_node": story.mapped_node,
        "max_depth": depth,
        "ripple_chain": chain,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map a fixture headline to a sourced ripple"
    )
    parser.add_argument("--fixture", default="threat_only_hormuz")
    parser.add_argument("--depth", type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(build_ripple(args.fixture, args.depth), indent=2))


if __name__ == "__main__":
    main()
