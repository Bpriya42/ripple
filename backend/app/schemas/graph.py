from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClaimState(StrEnum):
    OBSERVED_EFFECT = "observed_effect"
    ESTABLISHED_MECHANISM = "established_mechanism"
    EMERGING_SIGNAL = "emerging_signal"
    CONDITIONAL_PATHWAY = "conditional_pathway"
    NOT_SHOWN = "not_shown"


class Certainty(StrEnum):
    ESTABLISHED = "established"
    EMERGING = "emerging"
    SPECULATIVE = "speculative"


class Provenance(StrEnum):
    CURATED = "curated"
    AI_SUGGESTED = "ai_suggested"


class FixtureNode(StrictModel):
    id: str = Field(pattern=r"^[a-z]+\.[a-z0-9_]+$")
    type: str
    label: str
    aliases: list[str] = Field(default_factory=list)
    gdelt_tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FixtureEvidence(StrictModel):
    id: str = Field(pattern=r"^source\.[a-z0-9_]+$")
    title: str
    url: HttpUrl
    publisher: str
    type: str
    independent_group: str


class FixtureEdge(StrictModel):
    id: str = Field(pattern=r"^edge\.[a-z0-9_]+__[a-z0-9_]+$")
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    direction: str
    strength: str
    lag: str
    mechanism: str
    required_condition: str
    certainty: Certainty
    provenance: Provenance
    high_impact: bool = False
    evidence_ids: list[str] = Field(min_length=1)
    contested: bool = False
    contested_views: list[dict[str, Any]] = Field(default_factory=list)


class GraphFixture(StrictModel):
    fixture: bool
    version: str
    nodes: list[FixtureNode]
    evidence_sources: list[FixtureEvidence]
    edges: list[FixtureEdge] = Field(min_length=10)

    @model_validator(mode="after")
    def validate_references(self) -> GraphFixture:
        if not self.fixture:
            raise ValueError("Milestone 0 graph data must be explicitly marked as a fixture")
        node_ids = [node.id for node in self.nodes]
        evidence_ids = [source.id for source in self.evidence_sources]
        edge_ids = [edge.id for edge in self.edges]
        for label, values in (
            ("node", node_ids),
            ("evidence", evidence_ids),
            ("edge", edge_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {label} IDs")
        for edge in self.edges:
            if edge.from_node not in node_ids or edge.to_node not in node_ids:
                raise ValueError(f"edge {edge.id} references an unknown node")
            if not set(edge.evidence_ids).issubset(evidence_ids):
                raise ValueError(f"edge {edge.id} references unknown evidence")
        return self


class FixtureStorySource(StrictModel):
    outlet: str
    url: HttpUrl
    excerpt: str
    independent_group: str
    paywalled: bool = False


class FixtureStory(StrictModel):
    fixture: bool
    id: str
    headline: str
    published_at: datetime
    domain: str
    origin_location: str
    prominence_reasons: list[str]
    themes: list[str]
    entities: list[str]
    sources: list[FixtureStorySource] = Field(min_length=1)
    event_status: str
    mapped_node: str
    match_score: float = Field(ge=0, le=1)
    condition_met: bool
    direct_outcome_evidence: bool = False
