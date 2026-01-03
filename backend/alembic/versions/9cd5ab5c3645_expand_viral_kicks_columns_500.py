"""expand_viral_kicks_columns_500

Revision ID: 9cd5ab5c3645
Revises: 8cb7b73ef893
Create Date: 2026-01-04 04:55:47.685052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cd5ab5c3645'
down_revision: Union[str, Sequence[str], None] = 'e6f7g8h9i0j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Expand viral_kicks columns to match Pydantic schema (500 chars)."""
    # mechanism: 240 -> 500
    op.alter_column('viral_kicks', 'mechanism',
                    existing_type=sa.String(240),
                    type_=sa.String(500),
                    existing_nullable=False)
    
    # creator_instruction: 300 -> 500
    op.alter_column('viral_kicks', 'creator_instruction',
                    existing_type=sa.String(300),
                    type_=sa.String(500),
                    existing_nullable=True)


def downgrade() -> None:
    """Shrink viral_kicks columns back to original sizes."""
    op.alter_column('viral_kicks', 'mechanism',
                    existing_type=sa.String(500),
                    type_=sa.String(240),
                    existing_nullable=False)
    
    op.alter_column('viral_kicks', 'creator_instruction',
                    existing_type=sa.String(500),
                    type_=sa.String(300),
                    existing_nullable=True)
