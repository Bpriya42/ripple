import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]


def assert_no_unsupported_claims(payload: dict[str, Any]) -> None:
    for edge in payload.get("edges", []):
        assert edge.get("publish", True) is True
        assert edge.get("claim_state") != "not_shown"
        assert edge["evidence"]
        assert all(item["url"] for item in edge["evidence"])


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_feed_cursor_pagination(client: TestClient) -> None:
    first = client.get("/feed", params={"domain": "energy", "limit": 2})
    assert first.status_code == 200
    first_payload = first.json()
    assert len(first_payload["items"]) == 2
    assert first_payload["next_cursor"]
    assert all(item["fixture"] is True for item in first_payload["items"])
    assert all(item["sources"] for item in first_payload["items"])

    second = client.get(
        "/feed",
        params={"domain": "energy", "limit": 2, "cursor": first_payload["next_cursor"]},
    )
    assert second.status_code == 200
    second_ids = {item["story_id"] for item in second.json()["items"]}
    first_ids = {item["story_id"] for item in first_payload["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_feed_empty_and_invalid_cursor_states(client: TestClient) -> None:
    assert client.get("/feed", params={"domain": "not-a-fixture"}).json() == {
        "items": [],
        "next_cursor": None,
    }
    invalid = client.get("/feed", params={"cursor": "not-a-valid-cursor"})
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "invalid feed cursor"


def test_story_detail(client: TestClient) -> None:
    response = client.get("/story/story.fixture.threat_only_hormuz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["event_status"] == "threat_only"
    assert payload["mapped_nodes"] == ["event.hormuz_disruption"]
    assert payload["fixture"] is True
    assert payload["sources"][0]["url"].startswith("https://fixture.invalid/")
    assert client.get("/story/story.missing").status_code == 404


def test_threat_only_story_ripples_are_conditional(client: TestClient) -> None:
    response = client.get("/story/story.fixture.threat_only_hormuz/ripples")
    assert response.status_code == 200
    payload = response.json()
    assert payload["edges"]
    assert payload["main_path"]
    first_hop = [edge for edge in payload["edges"] if edge["hop"] == 1]
    assert first_hop
    assert all(edge["event_status"] == "threat_only" for edge in first_hop)
    assert all(edge["condition_met"] is False for edge in first_hop)
    assert all(edge["claim_state"] == "conditional_pathway" for edge in first_hop)
    assert all("required condition is not met" in edge["certainty_reasons"] for edge in first_hop)
    assert_no_unsupported_claims(payload)


def test_confirmed_story_uses_mechanism_without_claiming_observed_outcome(
    client: TestClient,
) -> None:
    payload = client.get("/story/story.fixture.confirmed_hormuz_disruption/ripples").json()
    first_hop = [edge for edge in payload["edges"] if edge["hop"] == 1]
    assert first_hop
    assert all(edge["condition_met"] is True for edge in first_hop)
    assert all(edge["claim_state"] == "established_mechanism" for edge in first_hop)
    assert all(edge["claim_state"] != "observed_effect" for edge in first_hop)
    assert_no_unsupported_claims(payload)


def test_story_ripple_cache_is_postgres_backed(client: TestClient) -> None:
    first = client.get("/story/story.fixture.threat_only_hormuz/ripples")
    second = client.get("/story/story.fixture.threat_only_hormuz/ripples")
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True


def test_concept_ripples_are_stable_mechanisms(client: TestClient) -> None:
    response = client.get("/concept/commodity.oil_price/ripples", params={"depth": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["concept_slug"] == "commodity.oil_price"
    assert payload["edges"]
    assert all("event_status" not in edge for edge in payload["edges"])
    assert_no_unsupported_claims(payload)
    assert client.get("/concept/concept.missing/ripples").status_code == 404


def test_edge_detail_contains_immediate_evidence(client: TestClient) -> None:
    response = client.get("/edge/edge.hormuz_disruption__oil_price")
    assert response.status_code == 200
    payload = response.json()
    assert payload["evidence"]
    assert payload["required_condition"]
    assert payload["provenance"] == "curated"
    assert client.get("/edge/edge.missing").status_code == 404


def test_depth_validation_and_openapi_contract(client: TestClient) -> None:
    assert client.get("/story/story.fixture.threat_only_hormuz/ripples?depth=4").status_code == 422
    openapi = client.get("/openapi.json").json()
    required_paths = {
        "/health",
        "/feed",
        "/story/{story_id}",
        "/story/{story_id}/ripples",
        "/concept/{node_slug}/ripples",
        "/edge/{edge_id}",
    }
    assert required_paths.issubset(openapi["paths"])
    committed = json.loads((ROOT / "docs" / "openapi.json").read_text(encoding="utf-8"))
    assert committed == app.openapi()
