"""Create the Milestone 0 relational schema.

Revision ID: 0001_milestone0
Revises: None
"""

from alembic import op

from app.db.base import Base
from app import models  # noqa: F401

revision = "0001_milestone0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=False)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=False)
