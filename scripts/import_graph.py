from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.session import build_engine
from app.models import Edge, EdgeEvidence, EvidenceSource, Node, NodeAlias
from app.services.graph import load_graph

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT / "data" / "graph" / "energy_v0.json"


def import_graph(path: Path = DEFAULT_GRAPH) -> tuple[int, int, int]:
    graph = load_graph(path)
    engine = build_engine()
    with Session(engine) as session, session.begin():
        for node in graph.nodes:
            session.execute(
                insert(Node)
                .values(
                    slug=node.id,
                    node_type=node.type,
                    label=node.label,
                    gdelt_tags=node.gdelt_tags,
                    node_metadata=node.metadata,
                    fixture=True,
                )
                .on_conflict_do_update(
                    index_elements=[Node.slug],
                    set_={
                        "node_type": node.type,
                        "label": node.label,
                        "gdelt_tags": node.gdelt_tags,
                        "node_metadata": node.metadata,
                        "fixture": True,
                    },
                )
            )
        nodes = {item.slug: item for item in session.scalars(select(Node)).all()}
        for node in graph.nodes:
            for alias in node.aliases:
                session.execute(
                    insert(NodeAlias)
                    .values(node_id=nodes[node.id].id, alias=alias)
                    .on_conflict_do_nothing(constraint="uq_node_alias")
                )

        for source in graph.evidence_sources:
            session.execute(
                insert(EvidenceSource)
                .values(
                    slug=source.id,
                    title=source.title,
                    url=str(source.url),
                    publisher=source.publisher,
                    source_type=source.type,
                    independent_group=source.independent_group,
                    fixture=True,
                )
                .on_conflict_do_update(
                    index_elements=[EvidenceSource.slug],
                    set_={
                        "title": source.title,
                        "url": str(source.url),
                        "publisher": source.publisher,
                        "source_type": source.type,
                        "independent_group": source.independent_group,
                        "fixture": True,
                    },
                )
            )
        sources = {
            item.slug: item for item in session.scalars(select(EvidenceSource)).all()
        }

        for edge in graph.edges:
            session.execute(
                insert(Edge)
                .values(
                    slug=edge.id,
                    from_node_id=nodes[edge.from_node].id,
                    to_node_id=nodes[edge.to_node].id,
                    direction=edge.direction,
                    strength=edge.strength,
                    lag=edge.lag,
                    mechanism=edge.mechanism,
                    required_condition=edge.required_condition,
                    certainty=edge.certainty.value,
                    provenance=edge.provenance.value,
                    high_impact=edge.high_impact,
                    contested=edge.contested,
                    contested_views=edge.contested_views,
                    fixture=True,
                )
                .on_conflict_do_update(
                    index_elements=[Edge.slug],
                    set_={
                        "direction": edge.direction,
                        "strength": edge.strength,
                        "lag": edge.lag,
                        "mechanism": edge.mechanism,
                        "required_condition": edge.required_condition,
                        "certainty": edge.certainty.value,
                        "provenance": edge.provenance.value,
                        "high_impact": edge.high_impact,
                        "contested": edge.contested,
                        "contested_views": edge.contested_views,
                        "fixture": True,
                    },
                )
            )
        edges = {item.slug: item for item in session.scalars(select(Edge)).all()}
        for edge in graph.edges:
            session.execute(
                delete(EdgeEvidence).where(EdgeEvidence.edge_id == edges[edge.id].id)
            )
            for evidence_id in edge.evidence_ids:
                session.add(
                    EdgeEvidence(
                        edge_id=edges[edge.id].id,
                        evidence_source_id=sources[evidence_id].id,
                        directness="mechanism",
                        supports=True,
                    )
                )
    return len(graph.nodes), len(graph.edges), len(graph.evidence_sources)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the versioned fixture graph")
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_GRAPH)
    args = parser.parse_args()
    node_count, edge_count, source_count = import_graph(args.path)
    print(
        f"Imported fixture graph: {node_count} nodes, {edge_count} edges, {source_count} sources"
    )


if __name__ == "__main__":
    main()
