"""add_temporal_fields_notebook_library

Revision ID: 2b6f5a1f0a1c
Revises: 6e9644c08b82
Create Date: 2026-01-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2b6f5a1f0a1c"
down_revision: Union[str, Sequence[str], None] = "6e9644c08b82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add temporal fields to notebook_library"""
    op.add_column("notebook_library", sa.Column("temporal_phase", sa.String(length=10), nullable=True))
    op.add_column("notebook_library", sa.Column("variant_age_days", sa.Integer(), nullable=True))
    op.add_column("notebook_library", sa.Column("novelty_decay_score", sa.Float(), nullable=True))
    op.add_column("notebook_library", sa.Column("burstiness_index", sa.Float(), nullable=True))
    op.create_index(
        op.f("ix_notebook_library_temporal_phase"),
        "notebook_library",
        ["temporal_phase"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema"""
    op.drop_index(op.f("ix_notebook_library_temporal_phase"), table_name="notebook_library")
    op.drop_column("notebook_library", "burstiness_index")
    op.drop_column("notebook_library", "novelty_decay_score")
    op.drop_column("notebook_library", "variant_age_days")
    op.drop_column("notebook_library", "temporal_phase")
