from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from app.schemas.graph import FixtureEdge, GraphFixture


def load_graph(path: Path) -> GraphFixture:
    return GraphFixture.model_validate_json(path.read_text(encoding="utf-8"))


def bounded_traversal(graph: GraphFixture, start_node: str, depth: int = 2) -> list[FixtureEdge]:
    if depth < 1 or depth > 3:
        raise ValueError("depth must be between 1 and 3")
    by_source: dict[str, list[FixtureEdge]] = {}
    for edge in graph.edges:
        by_source.setdefault(edge.from_node, []).append(edge)

    result: list[FixtureEdge] = []
    visited_edges: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(start_node, 0)])
    while queue:
        node_id, current_depth = queue.popleft()
        if current_depth >= depth:
            continue
        for edge in sorted(by_source.get(node_id, []), key=lambda candidate: candidate.id):
            if edge.id in visited_edges:
                continue
            visited_edges.add(edge.id)
            result.append(edge)
            queue.append((edge.to_node, current_depth + 1))
    return result


def graph_as_json(graph: GraphFixture) -> str:
    return json.dumps(graph.model_dump(mode="json", by_alias=True), indent=2, sort_keys=True)
