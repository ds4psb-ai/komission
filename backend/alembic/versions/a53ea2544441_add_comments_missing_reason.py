"""add_comments_missing_reason

Revision ID: a53ea2544441
Revises: 913f9d771734
Create Date: 2025-12-28 15:11:12.880717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a53ea2544441'
down_revision: Union[str, Sequence[str], None] = '913f9d771734'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add comments_missing_reason column to outlier_items."""
    op.add_column('outlier_items', sa.Column('comments_missing_reason', sa.String(length=200), nullable=True))


def downgrade() -> None:
    """Remove comments_missing_reason column from outlier_items."""
    op.drop_column('outlier_items', 'comments_missing_reason')
