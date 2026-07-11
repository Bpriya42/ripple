from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services.ingest.gdelt import (
    GdeltProvider,
    RecordedGdeltDocClient,
    parse_doc_response,
    parse_seendate,
)
from app.services.linker import LinkableNode, build_node_tag_index

ROOT = Path(__file__).resolve().parents[2]
RECORDED = ROOT / "data" / "fixtures" / "gdelt_doc_api_sample.json"

THEMES = ["ECON_OILPRICE", "MARITIME_CHOKEPOINT", "ENERGY_SECURITY", "MARITIME_INCIDENT"]
INDEX = build_node_tag_index(
    [
        LinkableNode("commodity.oil_price", ("ECON_OILPRICE",), has_outgoing_edges=True),
        LinkableNode("event.hormuz_disruption", ("MARITIME_CHOKEPOINT",), has_outgoing_edges=True),
        LinkableNode("event.gas_supply_disruption", ("ENERGY_SECURITY",), has_outgoing_edges=True),
        LinkableNode("event.shipping_disruption", ("MARITIME_INCIDENT",), has_outgoing_edges=True),
    ]
)
EDGE_COUNTS = {
    "commodity.oil_price": 6,
    "event.hormuz_disruption": 2,
    "event.gas_supply_disruption": 1,
    "event.shipping_disruption": 3,
}
NOW = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)


def test_parse_seendate_handles_compact_and_iso() -> None:
    assert parse_seendate("20260711T101500Z") == datetime(2026, 7, 11, 10, 15, tzinfo=UTC)
    assert parse_seendate("2026-07-11T10:15:00Z") == datetime(2026, 7, 11, 10, 15, tzinfo=UTC)


def test_parse_doc_response_tolerates_empty_and_invalid() -> None:
    assert parse_doc_response("") == []
    assert parse_doc_response("not json") == []
    assert parse_doc_response('{"noarticles": true}') == []


def test_recorded_client_rejects_unmarked_payload(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"queries": {}}', encoding="utf-8")
    with pytest.raises(ValueError, match="explicitly marked as a fixture"):
        RecordedGdeltDocClient(bad)


def _provider() -> GdeltProvider:
    return GdeltProvider(RecordedGdeltDocClient(RECORDED), INDEX, THEMES, EDGE_COUNTS, now=NOW)


def test_provider_dedupes_and_aggregates_themes() -> None:
    stories = _provider().fetch()
    assert len(stories) == 4  # the shared-URL article is collapsed to one story

    shared = next(s for s in stories if "reroute" in s.headline)
    assert shared.themes == ["ECON_OILPRICE", "MARITIME_CHOKEPOINT"]
    # Deterministic tie-break selects the alphabetically-first source node.
    assert shared.mapped_node == "commodity.oil_price"


def test_provider_never_asserts_an_outcome() -> None:
    stories = _provider().fetch()
    assert all(story.condition_met is False for story in stories)
    assert all(story.fixture is False for story in stories)
    assert all(story.slug.startswith("story.gdelt.") for story in stories)


def test_provider_classifies_event_status_from_headlines() -> None:
    by_node = {story.mapped_node: story for story in _provider().fetch()}
    assert by_node["event.shipping_disruption"].event_status == "disruption_reported"
    assert by_node["event.gas_supply_disruption"].event_status == "threat_only"


def test_provider_output_is_deterministic() -> None:
    first = [s.slug for s in _provider().fetch()]
    second = [s.slug for s in _provider().fetch()]
    assert first == second == sorted(first)
