"""merge_heads

Revision ID: 0ed31a82d1aa
Revises: a53ea2544441, c4d78e9f1a2b
Create Date: 2025-12-31 01:34:06.410746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ed31a82d1aa'
down_revision: Union[str, Sequence[str], None] = ('a53ea2544441', 'c4d78e9f1a2b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
