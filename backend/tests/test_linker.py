from datetime import UTC, datetime

from app.services.linker import (
    LinkableNode,
    build_node_tag_index,
    classify_event_status,
    live_prominence_reasons,
)

NODES = [
    LinkableNode("commodity.oil_price", ("ECON_OILPRICE",), has_outgoing_edges=True),
    LinkableNode("event.hormuz_disruption", ("MARITIME_CHOKEPOINT", "ECON_OIL"), True),
    LinkableNode("outcome.importer_inflation", ("ECON_INFLATION",), has_outgoing_edges=False),
    LinkableNode("outcome.consumer_price", ("ECON_INFLATION",), has_outgoing_edges=False),
]


def test_index_maps_known_theme_to_owning_node() -> None:
    index = build_node_tag_index(NODES)
    assert index.node_for_tags(["ECON_OILPRICE"]) == "commodity.oil_price"


def test_index_is_case_insensitive_and_order_independent() -> None:
    index = build_node_tag_index(NODES)
    assert index.node_for_tags(["econ_oilprice"]) == "commodity.oil_price"
    forward = index.node_for_tags(["ECON_OILPRICE", "MARITIME_CHOKEPOINT"])
    reverse = index.node_for_tags(["MARITIME_CHOKEPOINT", "ECON_OILPRICE"])
    assert forward == reverse == "commodity.oil_price"


def test_index_prefers_source_nodes_then_alphabetical() -> None:
    index = build_node_tag_index(NODES)
    # Both ECON_INFLATION owners lack outgoing edges, so the tie-break is the slug.
    assert index.node_for_tags(["ECON_INFLATION"]) == "outcome.consumer_price"


def test_index_returns_none_for_unknown_theme() -> None:
    index = build_node_tag_index(NODES)
    assert index.node_for_tags(["NOT_A_THEME"]) is None
    assert index.node_for_tags([]) is None


def test_threat_language_takes_precedence_and_never_meets_condition() -> None:
    status, condition_met = classify_event_status("Officials threaten to close the strait", "")
    assert status == "threat_only"
    assert condition_met is False


def test_disruption_language_without_threat() -> None:
    status, condition_met = classify_event_status("Port strike halts loading", "cargo rerouted")
    assert status == "disruption_reported"
    assert condition_met is False


def test_plain_report_defaults() -> None:
    status, condition_met = classify_event_status("Energy ministers meet in Vienna", "")
    assert status == "reported"
    assert condition_met is False


def test_prominence_reasons_are_transparent() -> None:
    now = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    fresh = live_prominence_reasons(
        published_at=datetime(2026, 7, 11, 11, 40, tzinfo=UTC),
        now=now,
        source_country="Germany",
        curated_edge_count=3,
    )
    assert fresh[0] == "live GDELT ingestion"
    assert "published within the hour" in fresh
    assert "3 curated mechanisms from the matched node" in fresh
    assert "origin: Germany" in fresh

    empty = live_prominence_reasons(
        published_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
        now=now,
        source_country="",
        curated_edge_count=0,
    )
    assert "older than a day" in empty
    assert "no established ripple yet" in empty
