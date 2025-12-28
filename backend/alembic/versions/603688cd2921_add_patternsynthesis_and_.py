"""Add PatternSynthesis and EvidenceSnapshot citation fields

Revision ID: 603688cd2921
Revises: 3c7f6b2g1d2e
Create Date: 2025-12-26 20:36:45.735271

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '603688cd2921'
down_revision: Union[str, Sequence[str], None] = '3c7f6b2g1d2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create pattern_syntheses table
    op.create_table('pattern_syntheses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('notebook_id', sa.String(length=255), nullable=True),
        sa.Column('source_sheet_url', sa.Text(), nullable=True),
        sa.Column('cluster_id', sa.String(length=100), nullable=False),
        sa.Column('temporal_phase', sa.String(length=20), nullable=True),
        sa.Column('synthesis_type', sa.Enum('INVARIANT_RULES', 'MUTATION_STRATEGY', 'FAILURE_MODES', 'AUDIENCE_SIGNAL', 'HOOK_PATTERN', 'DIRECTOR_INTENT', name='synthesistype'), nullable=False),
        sa.Column('synthesis_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_format', sa.String(length=20), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('source_pack_id', sa.UUID(), nullable=True),
        sa.Column('run_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.ForeignKeyConstraint(['source_pack_id'], ['notebook_source_packs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pattern_syntheses_cluster_id'), 'pattern_syntheses', ['cluster_id'], unique=False)
    op.create_index(op.f('ix_pattern_syntheses_notebook_id'), 'pattern_syntheses', ['notebook_id'], unique=False)
    op.create_index(op.f('ix_pattern_syntheses_synthesis_type'), 'pattern_syntheses', ['synthesis_type'], unique=False)
    op.create_index(op.f('ix_pattern_syntheses_temporal_phase'), 'pattern_syntheses', ['temporal_phase'], unique=False)
    
    # 2. Add columns to evidence_snapshots
    op.add_column('evidence_snapshots', sa.Column('notebooklm_citation', sa.Text(), nullable=True))
    op.add_column('evidence_snapshots', sa.Column('synthesis_source', sa.String(length=100), nullable=True))
    op.add_column('evidence_snapshots', sa.Column('synthesis_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_evidence_snapshots_synthesis_id', 'evidence_snapshots', 'pattern_syntheses', ['synthesis_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Remove evidence_snapshots columns
    op.drop_constraint('fk_evidence_snapshots_synthesis_id', 'evidence_snapshots', type_='foreignkey')
    op.drop_column('evidence_snapshots', 'synthesis_id')
    op.drop_column('evidence_snapshots', 'synthesis_source')
    op.drop_column('evidence_snapshots', 'notebooklm_citation')
    
    # 2. Drop pattern_syntheses table
    op.drop_index(op.f('ix_pattern_syntheses_temporal_phase'), table_name='pattern_syntheses')
    op.drop_index(op.f('ix_pattern_syntheses_synthesis_type'), table_name='pattern_syntheses')
    op.drop_index(op.f('ix_pattern_syntheses_notebook_id'), table_name='pattern_syntheses')
    op.drop_index(op.f('ix_pattern_syntheses_cluster_id'), table_name='pattern_syntheses')
    op.drop_table('pattern_syntheses')
    
    # 3. Drop enum type
    sa.Enum('INVARIANT_RULES', 'MUTATION_STRATEGY', 'FAILURE_MODES', 'AUDIENCE_SIGNAL', 'HOOK_PATTERN', 'DIRECTOR_INTENT', name='synthesistype').drop(op.get_bind(), checkfirst=True)
