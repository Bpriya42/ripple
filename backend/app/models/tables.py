from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Node(TimestampMixin, Base):
    __tablename__ = "nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    node_type: Mapped[str] = mapped_column(String(40), nullable=False)
    label: Mapped[str] = mapped_column(String(240), nullable=False)
    gdelt_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    node_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    fixture: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class NodeAlias(Base):
    __tablename__ = "node_aliases"
    __table_args__ = (UniqueConstraint("node_id", "alias", name="uq_node_alias"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(240), nullable=False, index=True)


class Edge(TimestampMixin, Base):
    __tablename__ = "edges"
    __table_args__ = (
        UniqueConstraint("from_node_id", "to_node_id", "direction", name="uq_edge_route"),
        Index("ix_edges_traversal", "from_node_id", "to_node_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    from_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    to_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String(40), nullable=False)
    strength: Mapped[str] = mapped_column(String(24), nullable=False)
    lag: Mapped[str] = mapped_column(String(24), nullable=False)
    mechanism: Mapped[str] = mapped_column(Text, nullable=False)
    required_condition: Mapped[str] = mapped_column(Text, nullable=False)
    certainty: Mapped[str] = mapped_column(String(24), nullable=False)
    provenance: Mapped[str] = mapped_column(String(24), nullable=False)
    high_impact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contested_views: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    fixture: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EvidenceSource(TimestampMixin, Base):
    __tablename__ = "evidence_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    independent_group: Mapped[str] = mapped_column(String(160), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fixture: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EdgeEvidence(Base):
    __tablename__ = "edge_evidence"
    __table_args__ = (UniqueConstraint("edge_id", "evidence_source_id", name="uq_edge_evidence"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    edge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("edges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    directness: Mapped[str] = mapped_column(String(32), nullable=False)
    supports: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Story(TimestampMixin, Base):
    __tablename__ = "stories"
    __table_args__ = (Index("ix_stories_feed", "domain", "published_at", "id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(40), nullable=False)
    event_status: Mapped[str] = mapped_column(String(48), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fixture: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class StorySource(Base):
    __tablename__ = "story_sources"
    __table_args__ = (UniqueConstraint("story_id", "url", name="uq_story_source_url"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    outlet: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    independent_group: Mapped[str] = mapped_column(String(160), nullable=False)


class StoryNodeMatch(Base):
    __tablename__ = "story_node_matches"
    __table_args__ = (UniqueConstraint("story_id", "node_id", name="uq_story_node_match"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_method: Mapped[str] = mapped_column(String(40), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)


class EventClaimResolution(TimestampMixin, Base):
    __tablename__ = "event_claim_resolutions"
    __table_args__ = (UniqueConstraint("story_id", "edge_id", name="uq_story_edge_resolution"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    edge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("edges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_status: Mapped[str] = mapped_column(String(48), nullable=False)
    required_condition: Mapped[str] = mapped_column(Text, nullable=False)
    condition_met: Mapped[bool] = mapped_column(Boolean, nullable=False)
    claim_state: Mapped[str] = mapped_column(String(40), nullable=False)
    certainty: Mapped[str] = mapped_column(String(24), nullable=False)
    certainty_reasons: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    publish: Mapped[bool] = mapped_column(Boolean, nullable=False)
    contested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RippleCache(Base):
    __tablename__ = "ripple_cache"
    __table_args__ = (UniqueConstraint("cache_key", name="uq_ripple_cache_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key: Mapped[str] = mapped_column(String(300), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (Index("ix_ingestion_runs_status_started", "status", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
