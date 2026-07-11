"""Create the immutable Milestone 0 relational schema.

Revision ID: 0001_milestone0
Revises: None
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_milestone0"
down_revision = None
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "nodes",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("slug", sa.String(160), unique=True, nullable=False),
        sa.Column("node_type", sa.String(40), nullable=False),
        sa.Column("label", sa.String(240), nullable=False),
        sa.Column("gdelt_tags", sa.JSON(), nullable=False),
        sa.Column("node_metadata", sa.JSON(), nullable=False),
        sa.Column("fixture", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "evidence_sources",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("slug", sa.String(180), unique=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("publisher", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("independent_group", sa.String(160), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fixture", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "stories",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("slug", sa.String(220), unique=True, nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(40), nullable=False),
        sa.Column("event_status", sa.String(48), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fixture", sa.Boolean(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_stories_feed", "stories", ["domain", "published_at", "id"])
    op.create_table(
        "ripple_cache",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("cache_key", sa.String(300), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("cache_key", name="uq_ripple_cache_key"),
    )
    op.create_index("ix_ripple_cache_expires_at", "ripple_cache", ["expires_at"])
    op.create_table(
        "ingestion_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("run_key", sa.String(200), unique=True, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_seen", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_ingestion_runs_status_started", "ingestion_runs", ["status", "started_at"])
    op.create_table(
        "edges",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("slug", sa.String(220), unique=True, nullable=False),
        sa.Column(
            "from_node_id", UUID, sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "to_node_id", UUID, sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("direction", sa.String(40), nullable=False),
        sa.Column("strength", sa.String(24), nullable=False),
        sa.Column("lag", sa.String(24), nullable=False),
        sa.Column("mechanism", sa.Text(), nullable=False),
        sa.Column("required_condition", sa.Text(), nullable=False),
        sa.Column("certainty", sa.String(24), nullable=False),
        sa.Column("provenance", sa.String(24), nullable=False),
        sa.Column("high_impact", sa.Boolean(), nullable=False),
        sa.Column("contested", sa.Boolean(), nullable=False),
        sa.Column("contested_views", sa.JSON(), nullable=False),
        sa.Column("fixture", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("from_node_id", "to_node_id", "direction", name="uq_edge_route"),
    )
    op.create_index("ix_edges_traversal", "edges", ["from_node_id", "to_node_id"])
    op.create_table(
        "node_aliases",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("node_id", UUID, sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(240), nullable=False),
        sa.UniqueConstraint("node_id", "alias", name="uq_node_alias"),
    )
    op.create_index("ix_node_aliases_node_id", "node_aliases", ["node_id"])
    op.create_index("ix_node_aliases_alias", "node_aliases", ["alias"])
    op.create_table(
        "story_sources",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "story_id", UUID, sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("outlet", sa.String(200), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("independent_group", sa.String(160), nullable=False),
        sa.UniqueConstraint("story_id", "url", name="uq_story_source_url"),
    )
    op.create_index("ix_story_sources_story_id", "story_sources", ["story_id"])
    op.create_table(
        "story_node_matches",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "story_id", UUID, sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("node_id", UUID, sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_method", sa.String(40), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.UniqueConstraint("story_id", "node_id", name="uq_story_node_match"),
    )
    op.create_index("ix_story_node_matches_story_id", "story_node_matches", ["story_id"])
    op.create_index("ix_story_node_matches_node_id", "story_node_matches", ["node_id"])
    op.create_table(
        "edge_evidence",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("edge_id", UUID, sa.ForeignKey("edges.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "evidence_source_id",
            UUID,
            sa.ForeignKey("evidence_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("directness", sa.String(32), nullable=False),
        sa.Column("supports", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("edge_id", "evidence_source_id", name="uq_edge_evidence"),
    )
    op.create_index("ix_edge_evidence_edge_id", "edge_evidence", ["edge_id"])
    op.create_index("ix_edge_evidence_evidence_source_id", "edge_evidence", ["evidence_source_id"])
    op.create_table(
        "event_claim_resolutions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "story_id", UUID, sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("edge_id", UUID, sa.ForeignKey("edges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_status", sa.String(48), nullable=False),
        sa.Column("required_condition", sa.Text(), nullable=False),
        sa.Column("condition_met", sa.Boolean(), nullable=False),
        sa.Column("claim_state", sa.String(40), nullable=False),
        sa.Column("certainty", sa.String(24), nullable=False),
        sa.Column("certainty_reasons", sa.JSON(), nullable=False),
        sa.Column("publish", sa.Boolean(), nullable=False),
        sa.Column("contested", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("story_id", "edge_id", name="uq_story_edge_resolution"),
    )
    op.create_index("ix_event_claim_resolutions_story_id", "event_claim_resolutions", ["story_id"])
    op.create_index("ix_event_claim_resolutions_edge_id", "event_claim_resolutions", ["edge_id"])


def downgrade() -> None:
    op.drop_table("event_claim_resolutions")
    op.drop_table("edge_evidence")
    op.drop_table("story_node_matches")
    op.drop_table("story_sources")
    op.drop_table("node_aliases")
    op.drop_table("edges")
    op.drop_table("ingestion_runs")
    op.drop_table("ripple_cache")
    op.drop_table("stories")
    op.drop_table("evidence_sources")
    op.drop_table("nodes")
