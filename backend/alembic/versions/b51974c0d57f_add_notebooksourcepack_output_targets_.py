"""Add NotebookSourcePack output_targets pack_mode schema_version

Revision ID: b51974c0d57f
Revises: ebae37e56cec
Create Date: 2025-12-26 20:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b51974c0d57f'
down_revision: Union[str, Sequence[str], None] = 'ebae37e56cec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add Phase C: Multi-Output Protocol fields to NotebookSourcePack
    op.add_column('notebook_source_packs', sa.Column('output_targets', sa.String(length=100), nullable=True))
    op.add_column('notebook_source_packs', sa.Column('pack_mode', sa.String(length=20), nullable=True))
    op.add_column('notebook_source_packs', sa.Column('schema_version', sa.String(length=10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('notebook_source_packs', 'schema_version')
    op.drop_column('notebook_source_packs', 'pack_mode')
    op.drop_column('notebook_source_packs', 'output_targets')
