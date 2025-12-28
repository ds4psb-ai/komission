"""merge_heads

Revision ID: 913f9d771734
Revises: 0034103f8b37, 2249e3214282
Create Date: 2025-12-28 15:10:51.350655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '913f9d771734'
down_revision: Union[str, Sequence[str], None] = ('0034103f8b37', '2249e3214282')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
