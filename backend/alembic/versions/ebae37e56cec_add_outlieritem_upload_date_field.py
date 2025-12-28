"""Add OutlierItem upload_date field

Revision ID: ebae37e56cec
Revises: 603688cd2921
Create Date: 2025-12-26 20:40:30.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ebae37e56cec'
down_revision: Union[str, Sequence[str], None] = '603688cd2921'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add upload_date column to outlier_items
    op.add_column('outlier_items', sa.Column('upload_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('outlier_items', 'upload_date')
