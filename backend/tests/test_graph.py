from pathlib import Path

import pytest

from app.services.graph import bounded_traversal, load_graph

ROOT = Path(__file__).resolve().parents[2]


def test_fixture_graph_has_phase_one_sourced_edges() -> None:
    graph = load_graph(ROOT / "data" / "graph" / "energy_v0.json")
    assert graph.fixture is True
    assert 30 <= len(graph.edges) <= 50
    assert all(edge.evidence_ids for edge in graph.edges)
    assert all(edge.required_condition for edge in graph.edges)


def test_bounded_traversal_stops_at_requested_depth() -> None:
    graph = load_graph(ROOT / "data" / "graph" / "energy_v0.json")
    one_hop = bounded_traversal(graph, "event.hormuz_disruption", depth=1)
    two_hops = bounded_traversal(graph, "event.hormuz_disruption", depth=2)
    assert {edge.id for edge in one_hop} == {
        "edge.hormuz_disruption__lng_availability",
        "edge.hormuz_disruption__oil_price",
    }
    assert len(two_hops) > len(one_hop)
    assert "edge.transport_cost__food_price" not in {edge.id for edge in two_hops}


@pytest.mark.parametrize("depth", [0, 4])
def test_bounded_traversal_rejects_out_of_contract_depth(depth: int) -> None:
    graph = load_graph(ROOT / "data" / "graph" / "energy_v0.json")
    with pytest.raises(ValueError, match="between 1 and 3"):
        bounded_traversal(graph, "event.hormuz_disruption", depth=depth)
