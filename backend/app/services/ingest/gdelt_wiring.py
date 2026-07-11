"""Build linker inputs from the persisted curated graph.

This bridges the ORM to the pure, ORM-free linker so both the ingestion CLI and
the manual pull script share one deterministic mapping of live GDELT themes to
curated nodes.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Edge, Node
from app.services.linker import LinkableNode, NodeTagIndex, build_node_tag_index


@dataclass(frozen=True)
class GraphLinkContext:
    index: NodeTagIndex
    themes: list[str]
    edge_counts: dict[str, int]


def load_graph_link_context(session: Session) -> GraphLinkContext:
    nodes = session.scalars(select(Node)).all()
    edges = session.scalars(select(Edge)).all()

    slug_by_id = {node.id: node.slug for node in nodes}
    edge_counts: dict[str, int] = {}
    for edge in edges:
        slug = slug_by_id.get(edge.from_node_id)
        if slug is not None:
            edge_counts[slug] = edge_counts.get(slug, 0) + 1

    linkables = [
        LinkableNode(
            slug=node.slug,
            gdelt_tags=tuple(node.gdelt_tags),
            has_outgoing_edges=edge_counts.get(node.slug, 0) > 0,
        )
        for node in nodes
    ]
    themes = sorted({tag for node in nodes for tag in node.gdelt_tags})
    return GraphLinkContext(
        index=build_node_tag_index(linkables),
        themes=themes,
        edge_counts=edge_counts,
    )
