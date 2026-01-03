"""add_creator_username_to_outlier_items

Revision ID: e6f7g8h9i0j1
Revises: 6e90df2c244e
Create Date: 2026-01-04 00:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e6f7g8h9i0j1'
down_revision = '6e90df2c244e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add creator_username column to outlier_items table
    op.add_column('outlier_items', sa.Column('creator_username', sa.String(100), nullable=True))
    
    # Migrate existing data from raw_payload.creator_username
    op.execute("""
        UPDATE outlier_items 
        SET creator_username = raw_payload->>'creator_username'
        WHERE raw_payload->>'creator_username' IS NOT NULL
        AND creator_username IS NULL
    """)


def downgrade() -> None:
    op.drop_column('outlier_items', 'creator_username')
