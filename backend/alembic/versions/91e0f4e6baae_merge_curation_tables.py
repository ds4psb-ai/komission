"""merge curation tables

Revision ID: 91e0f4e6baae
Revises: 0ed31a82d1aa, d5f8a1c2b3e4
Create Date: 2025-12-31 17:01:19.702354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91e0f4e6baae'
down_revision: Union[str, Sequence[str], None] = ('0ed31a82d1aa', 'd5f8a1c2b3e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
