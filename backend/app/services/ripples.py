from __future__ import annotations

from pydantic import HttpUrl

from app.models import Edge, EdgeEvidence, EventClaimResolution, EvidenceSource, Node
from app.schemas.api import (
    ConceptRippleEdgeResponse,
    ConceptRippleResponse,
    EdgeDetailResponse,
    EvidenceResponse,
    RippleNodeResponse,
    StoryRippleEdgeResponse,
    StoryRippleResponse,
)
from app.schemas.graph import Certainty, ClaimState, Provenance
from app.services.cache import PostgresRippleCache
from app.services.publication_policy import PolicyDecision, PolicyInput, evaluate_publication
from app.services.repositories import GraphRepository, StoryRepository


def node_response(node: Node) -> RippleNodeResponse:
    return RippleNodeResponse(node_id=node.slug, label=node.label, node_type=node.node_type)


def evidence_response(pair: tuple[EdgeEvidence, EvidenceSource]) -> EvidenceResponse:
    edge_evidence, source = pair
    return EvidenceResponse(
        evidence_id=source.slug,
        title=source.title,
        url=HttpUrl(source.url),
        publisher=source.publisher,
        source_type=source.source_type,
        directness=edge_evidence.directness,
        supports=edge_evidence.supports,
    )


class RippleService:
    CACHE_VERSION = "v2"

    def __init__(
        self,
        stories: StoryRepository,
        graph: GraphRepository,
        cache: PostgresRippleCache,
    ) -> None:
        self.stories = stories
        self.graph = graph
        self.cache = cache

    def story_ripples(self, story_slug: str, depth: int) -> StoryRippleResponse | None:
        key = f"{self.CACHE_VERSION}:story:{story_slug}:depth:{depth}"
        cached = self.cache.get(key)
        if cached is not None:
            cached["cached"] = True
            return StoryRippleResponse.model_validate(cached)

        story = self.stories.get(story_slug)
        if story is None:
            return None
        matched = self.stories.matched_nodes(story.id)
        if not matched:
            response = StoryRippleResponse(
                story_id=story.slug,
                fixture=story.fixture,
                max_depth=depth,
                nodes=[],
                edges=[],
                main_path=[],
                branches=[],
            )
            self.cache.set(key, response.model_dump(mode="json"))
            return response

        traversed = self.graph.traverse(matched[0].id, depth)
        nodes = self.graph.nodes_by_id()
        evidence = self.graph.evidence([item.edge.id for item in traversed])
        resolutions = self.stories.resolutions(story.id)
        response_edges: list[StoryRippleEdgeResponse] = []
        for item in traversed:
            edge = item.edge
            edge_evidence = evidence[edge.id]
            if not edge_evidence:
                continue
            resolution = resolutions.get(edge.id)
            decision = self._story_decision(edge, edge_evidence, resolution)
            if not decision.publish or decision.claim_state is ClaimState.NOT_SHOWN:
                continue
            response_edges.append(
                StoryRippleEdgeResponse(
                    edge_id=edge.slug,
                    story_id=story.slug,
                    from_node=nodes[edge.from_node_id].slug,
                    to_node=nodes[edge.to_node_id].slug,
                    direction=edge.direction,
                    strength=edge.strength,
                    lag=edge.lag,
                    mechanism=edge.mechanism,
                    event_status=story.event_status,
                    required_condition=edge.required_condition,
                    condition_met=resolution.condition_met if resolution else False,
                    claim_state=decision.claim_state,
                    certainty=decision.certainty,
                    certainty_reasons=list(decision.certainty_reasons),
                    provenance=Provenance(edge.provenance),
                    high_impact=edge.high_impact,
                    evidence=[evidence_response(pair) for pair in edge_evidence],
                    contested=decision.contested,
                    publish=True,
                    hop=item.hop,
                )
            )

        main_path, branches = self._paths(response_edges)
        used_node_ids = {matched[0].id}
        for item in traversed:
            if any(response_edge.edge_id == item.edge.slug for response_edge in response_edges):
                used_node_ids.update((item.edge.from_node_id, item.edge.to_node_id))
        response = StoryRippleResponse(
            story_id=story.slug,
            fixture=story.fixture,
            max_depth=depth,
            nodes=[
                node_response(nodes[item])
                for item in sorted(used_node_ids, key=lambda node_id: nodes[node_id].slug)
            ],
            edges=response_edges,
            main_path=main_path,
            branches=branches,
        )
        self.cache.set(key, response.model_dump(mode="json"))
        return response

    def concept_ripples(self, concept_slug: str, depth: int) -> ConceptRippleResponse | None:
        key = f"{self.CACHE_VERSION}:concept:{concept_slug}:depth:{depth}"
        cached = self.cache.get(key)
        if cached is not None:
            cached["cached"] = True
            return ConceptRippleResponse.model_validate(cached)
        concept = self.graph.get_node(concept_slug)
        if concept is None:
            return None
        traversed = self.graph.traverse(concept.id, depth)
        nodes = self.graph.nodes_by_id()
        evidence = self.graph.evidence([item.edge.id for item in traversed])
        response_edges: list[ConceptRippleEdgeResponse] = []
        used_node_ids = {concept.id}
        for item in traversed:
            edge_evidence = evidence[item.edge.id]
            if not self._eligible_stable_edge(item.edge, edge_evidence):
                continue
            edge = item.edge
            used_node_ids.update((edge.from_node_id, edge.to_node_id))
            response_edges.append(
                ConceptRippleEdgeResponse(
                    edge_id=edge.slug,
                    from_node=nodes[edge.from_node_id].slug,
                    to_node=nodes[edge.to_node_id].slug,
                    direction=edge.direction,
                    strength=edge.strength,
                    lag=edge.lag,
                    mechanism=edge.mechanism,
                    required_condition=edge.required_condition,
                    certainty=Certainty(edge.certainty),
                    provenance=Provenance(edge.provenance),
                    high_impact=edge.high_impact,
                    evidence=[evidence_response(pair) for pair in edge_evidence],
                    contested=edge.contested,
                    hop=item.hop,
                )
            )
        response = ConceptRippleResponse(
            concept_slug=concept.slug,
            max_depth=depth,
            nodes=[
                node_response(nodes[item])
                for item in sorted(used_node_ids, key=lambda node_id: nodes[node_id].slug)
            ],
            edges=response_edges,
        )
        self.cache.set(key, response.model_dump(mode="json"))
        return response

    def edge_detail(self, edge_slug: str) -> EdgeDetailResponse | None:
        edge = self.graph.get_edge(edge_slug)
        if edge is None:
            return None
        edge_evidence = self.graph.evidence([edge.id])[edge.id]
        if not self._eligible_stable_edge(edge, edge_evidence):
            return None
        nodes = self.graph.nodes_by_id()
        return EdgeDetailResponse(
            edge_id=edge.slug,
            from_node=node_response(nodes[edge.from_node_id]),
            to_node=node_response(nodes[edge.to_node_id]),
            direction=edge.direction,
            strength=edge.strength,
            lag=edge.lag,
            mechanism=edge.mechanism,
            required_condition=edge.required_condition,
            certainty=Certainty(edge.certainty),
            provenance=Provenance(edge.provenance),
            high_impact=edge.high_impact,
            evidence=[evidence_response(pair) for pair in edge_evidence],
            contested=edge.contested,
            contested_views=edge.contested_views,
        )

    @staticmethod
    def _story_decision(
        edge: Edge,
        edge_evidence: list[tuple[EdgeEvidence, EvidenceSource]],
        resolution: EventClaimResolution | None,
    ) -> PolicyDecision:
        if resolution is not None:
            return evaluate_publication(
                PolicyInput(
                    provenance=Provenance(edge.provenance),
                    condition_met=resolution.condition_met,
                    direct_outcome_evidence=(
                        resolution.claim_state == ClaimState.OBSERVED_EFFECT.value
                    ),
                    independent_source_count=len(
                        {source.independent_group for _, source in edge_evidence}
                    ),
                    high_impact=edge.high_impact,
                    contradiction=edge.contested,
                    contradiction_can_be_presented=bool(edge.contested_views),
                )
            )
        return evaluate_publication(
            PolicyInput(
                provenance=Provenance(edge.provenance),
                condition_met=False,
                independent_source_count=len(
                    {source.independent_group for _, source in edge_evidence}
                ),
                high_impact=edge.high_impact,
                contradiction=edge.contested,
                contradiction_can_be_presented=bool(edge.contested_views),
            )
        )

    @staticmethod
    def _eligible_stable_edge(
        edge: Edge, edge_evidence: list[tuple[EdgeEvidence, EvidenceSource]]
    ) -> bool:
        if not edge_evidence:
            return False
        if edge.contested and not edge.contested_views:
            return False
        if edge.provenance == Provenance.CURATED.value:
            return True
        threshold = 3 if edge.high_impact else 2
        return len({source.independent_group for _, source in edge_evidence}) >= threshold

    @staticmethod
    def _paths(edges: list[StoryRippleEdgeResponse]) -> tuple[list[str], list[list[str]]]:
        if not edges:
            return [], []
        by_from: dict[str, list[StoryRippleEdgeResponse]] = {}
        for edge in edges:
            by_from.setdefault(edge.from_node, []).append(edge)
        for candidates in by_from.values():
            candidates.sort(key=lambda item: item.edge_id)
        first = sorted((edge for edge in edges if edge.hop == 1), key=lambda item: item.edge_id)
        if not first:
            return [], [[edge.edge_id] for edge in edges]
        main: list[str] = []
        current = first[0]
        while True:
            main.append(current.edge_id)
            next_edges = by_from.get(current.to_node, [])
            if not next_edges:
                break
            current = next_edges[0]
        branches = [[edge.edge_id] for edge in edges if edge.edge_id not in main]
        return main, branches
