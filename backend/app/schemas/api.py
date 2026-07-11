from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, Field, HttpUrl

from app.schemas.graph import Certainty, ClaimState, Provenance, StrictModel


class ApiModel(StrictModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class HealthResponse(ApiModel):
    status: str
    database: str


class StorySourceResponse(ApiModel):
    outlet: str
    url: HttpUrl
    excerpt: str
    paywalled: bool


class FeedItemResponse(ApiModel):
    story_id: str
    headline: str
    published_at: datetime
    origin_location: str
    sources: list[StorySourceResponse]
    domain: str
    prominence_reasons: list[str]
    fixture: bool


class FeedResponse(ApiModel):
    items: list[FeedItemResponse]
    next_cursor: str | None = None


class StoryDetailResponse(FeedItemResponse):
    event_status: str
    themes: list[str]
    entities: list[str]
    mapped_nodes: list[str]


class EvidenceResponse(ApiModel):
    evidence_id: str
    title: str
    url: HttpUrl
    publisher: str
    source_type: str
    directness: str
    supports: bool


class RippleNodeResponse(ApiModel):
    node_id: str
    label: str
    node_type: str


class StoryRippleEdgeResponse(ApiModel):
    edge_id: str
    story_id: str
    from_node: str
    to_node: str
    direction: str
    strength: str
    lag: str
    mechanism: str
    event_status: str
    required_condition: str
    condition_met: bool
    claim_state: ClaimState
    certainty: Certainty
    certainty_reasons: list[str]
    provenance: Provenance
    evidence: list[EvidenceResponse] = Field(min_length=1)
    contested: bool
    publish: bool
    hop: int = Field(ge=1, le=3)


class StoryRippleResponse(ApiModel):
    story_id: str
    fixture: bool
    max_depth: int
    nodes: list[RippleNodeResponse]
    edges: list[StoryRippleEdgeResponse]
    main_path: list[str]
    branches: list[list[str]]
    cached: bool = False


class ConceptRippleEdgeResponse(ApiModel):
    edge_id: str
    from_node: str
    to_node: str
    direction: str
    strength: str
    lag: str
    mechanism: str
    required_condition: str
    certainty: Certainty
    provenance: Provenance
    evidence: list[EvidenceResponse] = Field(min_length=1)
    contested: bool
    hop: int = Field(ge=1, le=3)


class ConceptRippleResponse(ApiModel):
    concept_slug: str
    max_depth: int
    nodes: list[RippleNodeResponse]
    edges: list[ConceptRippleEdgeResponse]
    cached: bool = False


class EdgeDetailResponse(ApiModel):
    edge_id: str
    from_node: RippleNodeResponse
    to_node: RippleNodeResponse
    direction: str
    strength: str
    lag: str
    mechanism: str
    required_condition: str
    certainty: Certainty
    provenance: Provenance
    evidence: list[EvidenceResponse] = Field(min_length=1)
    contested: bool
    contested_views: list[dict[str, object]]


class ErrorResponse(ApiModel):
    detail: str
