"""Add Milestone 1 feed and source fields.

Revision ID: 0002_milestone1
Revises: 0001_milestone0
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_milestone1"
down_revision = "0001_milestone0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stories",
        sa.Column(
            "origin_location", sa.String(length=240), nullable=False, server_default="Unknown"
        ),
    )
    op.add_column(
        "stories",
        sa.Column("prominence_reasons", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column("stories", sa.Column("themes", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("stories", sa.Column("entities", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column(
        "story_sources",
        sa.Column("paywalled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("story_sources", "paywalled")
    op.drop_column("stories", "entities")
    op.drop_column("stories", "themes")
    op.drop_column("stories", "prominence_reasons")
    op.drop_column("stories", "origin_location")
