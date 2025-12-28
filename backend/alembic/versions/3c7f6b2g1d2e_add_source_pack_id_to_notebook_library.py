"""add_source_pack_id_to_notebook_library

Revision ID: 3c7f6b2g1d2e
Revises: 2b6f5a1f0a1c
Create Date: 2025-12-26 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3c7f6b2g1d2e"
down_revision: Union[str, Sequence[str], None] = "0bd2231d0fb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add source_pack_id to notebook_library"""
    op.add_column(
        "notebook_library",
        sa.Column("source_pack_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_notebook_library_source_pack",
        "notebook_library",
        "notebook_source_packs",
        ["source_pack_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema"""
    op.drop_constraint("fk_notebook_library_source_pack", "notebook_library", type_="foreignkey")
    op.drop_column("notebook_library", "source_pack_id")
