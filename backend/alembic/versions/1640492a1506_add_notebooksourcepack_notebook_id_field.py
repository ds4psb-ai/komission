"""Add NotebookSourcePack notebook_id field

Revision ID: 1640492a1506
Revises: b51974c0d57f
Create Date: 2025-12-26 20:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1640492a1506'
down_revision: Union[str, Sequence[str], None] = 'b51974c0d57f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add notebook_id column to notebook_source_packs
    op.add_column('notebook_source_packs', sa.Column('notebook_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('notebook_source_packs', 'notebook_id')
