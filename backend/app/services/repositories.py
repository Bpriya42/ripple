from __future__ import annotations

import base64
import json
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Edge,
    EdgeEvidence,
    EventClaimResolution,
    EvidenceSource,
    Node,
    Story,
    StoryNodeMatch,
    StorySource,
)


class InvalidCursorError(ValueError):
    pass


@dataclass(frozen=True)
class TraversedEdge:
    edge: Edge
    hop: int


def encode_cursor(story: Story) -> str:
    raw = json.dumps([story.published_at.isoformat(), str(story.id)], separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        padding = "=" * (-len(cursor) % 4)
        published, story_id = json.loads(base64.urlsafe_b64decode(cursor + padding))
        return datetime.fromisoformat(published), uuid.UUID(story_id)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidCursorError("invalid feed cursor") from exc


class StoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_feed(
        self, domain: str, limit: int, cursor: str | None
    ) -> tuple[list[Story], str | None]:
        statement = select(Story).where(Story.domain == domain)
        if cursor:
            published_at, story_id = decode_cursor(cursor)
            statement = statement.where(
                or_(
                    Story.published_at < published_at,
                    and_(Story.published_at == published_at, Story.id < story_id),
                )
            )
        stories = list(
            self.session.scalars(
                statement.order_by(Story.published_at.desc(), Story.id.desc()).limit(limit + 1)
            ).all()
        )
        has_more = len(stories) > limit
        page = stories[:limit]
        next_cursor = encode_cursor(page[-1]) if has_more and page else None
        return page, next_cursor

    def get(self, slug: str) -> Story | None:
        return self.session.scalar(select(Story).where(Story.slug == slug))

    def sources(self, story_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[StorySource]]:
        grouped: dict[uuid.UUID, list[StorySource]] = defaultdict(list)
        if not story_ids:
            return grouped
        for source in self.session.scalars(
            select(StorySource)
            .where(StorySource.story_id.in_(story_ids))
            .order_by(StorySource.outlet)
        ).all():
            grouped[source.story_id].append(source)
        return grouped

    def matched_nodes(self, story_id: uuid.UUID) -> list[Node]:
        return list(
            self.session.scalars(
                select(Node)
                .join(StoryNodeMatch, StoryNodeMatch.node_id == Node.id)
                .where(StoryNodeMatch.story_id == story_id)
                .order_by(StoryNodeMatch.score.desc(), Node.slug)
            ).all()
        )

    def resolutions(self, story_id: uuid.UUID) -> dict[uuid.UUID, EventClaimResolution]:
        return {
            item.edge_id: item
            for item in self.session.scalars(
                select(EventClaimResolution).where(EventClaimResolution.story_id == story_id)
            ).all()
        }


class GraphRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_node(self, slug: str) -> Node | None:
        return self.session.scalar(select(Node).where(Node.slug == slug))

    def get_edge(self, slug: str) -> Edge | None:
        return self.session.scalar(select(Edge).where(Edge.slug == slug))

    def nodes_by_id(self) -> dict[uuid.UUID, Node]:
        return {node.id: node for node in self.session.scalars(select(Node)).all()}

    def traverse(self, start_node_id: uuid.UUID, depth: int) -> list[TraversedEdge]:
        if depth < 1 or depth > 3:
            raise ValueError("depth must be between 1 and 3")
        edges = list(self.session.scalars(select(Edge).order_by(Edge.slug)).all())
        by_source: dict[uuid.UUID, list[Edge]] = defaultdict(list)
        for edge in edges:
            by_source[edge.from_node_id].append(edge)
        result: list[TraversedEdge] = []
        visited: set[uuid.UUID] = set()
        queue: deque[tuple[uuid.UUID, int]] = deque([(start_node_id, 0)])
        while queue:
            node_id, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            for edge in by_source[node_id]:
                if edge.id in visited:
                    continue
                visited.add(edge.id)
                hop = current_depth + 1
                result.append(TraversedEdge(edge=edge, hop=hop))
                queue.append((edge.to_node_id, hop))
        return result

    def evidence(
        self, edge_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[tuple[EdgeEvidence, EvidenceSource]]]:
        grouped: dict[uuid.UUID, list[tuple[EdgeEvidence, EvidenceSource]]] = defaultdict(list)
        if not edge_ids:
            return grouped
        rows = self.session.execute(
            select(EdgeEvidence, EvidenceSource)
            .join(EvidenceSource, EvidenceSource.id == EdgeEvidence.evidence_source_id)
            .where(EdgeEvidence.edge_id.in_(edge_ids))
            .order_by(EvidenceSource.publisher, EvidenceSource.title)
        ).all()
        for edge_evidence, source in rows:
            grouped[edge_evidence.edge_id].append((edge_evidence, source))
        return grouped
