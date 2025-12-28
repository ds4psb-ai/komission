"""P0_4_5_pattern_library_evidence_loop

Revision ID: 0bd2231d0fb6
Revises: 910b7429e156
Create Date: 2025-12-26 14:07:45.678901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0bd2231d0fb6'
down_revision: Union[str, Sequence[str], None] = '910b7429e156'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - P0-4, P0-5 models"""
    # P0-4: Update notebook_source_packs
    op.add_column('notebook_source_packs', sa.Column('temporal_phase', sa.String(length=20), nullable=True))
    op.add_column('notebook_source_packs', sa.Column('inputs_hash', sa.String(length=64), nullable=True))
    op.add_column('notebook_source_packs', sa.Column('run_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_notebook_source_packs_temporal_phase'), 'notebook_source_packs', ['temporal_phase'], unique=False)
    op.create_foreign_key('fk_notebook_source_packs_run_id', 'notebook_source_packs', 'runs', ['run_id'], ['id'])
    
    # P0-4: Create pattern_library table
    op.create_table(
        'pattern_library',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('pattern_id', sa.String(length=100), nullable=False),
        sa.Column('source_pack_id', sa.UUID(), nullable=True),
        sa.Column('cluster_id', sa.String(length=100), nullable=False),
        sa.Column('temporal_phase', sa.String(length=20), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('invariant_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('mutation_strategy', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('previous_revision_id', sa.UUID(), nullable=True),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_success_rate', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('run_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_pack_id'], ['notebook_source_packs.id'], ),
        sa.ForeignKeyConstraint(['previous_revision_id'], ['pattern_library.id'], ),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pattern_library_pattern_id'), 'pattern_library', ['pattern_id'], unique=True)
    op.create_index(op.f('ix_pattern_library_cluster_id'), 'pattern_library', ['cluster_id'], unique=False)
    op.create_index(op.f('ix_pattern_library_temporal_phase'), 'pattern_library', ['temporal_phase'], unique=False)
    
    # P0-5: Create evidence_events table
    op.create_table(
        'evidence_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('run_id', sa.UUID(), nullable=True),
        sa.Column('parent_node_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.Enum('QUEUED', 'RUNNING', 'EVIDENCE_READY', 'DECIDED', 'EXECUTED', 'MEASURED', 'FAILED', name='evidenceeventstatus'), nullable=False),
        sa.Column('evidence_snapshot_id', sa.UUID(), nullable=True),
        sa.Column('decision_object_id', sa.UUID(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('queued_at', sa.DateTime(), nullable=False),
        sa.Column('evidence_ready_at', sa.DateTime(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('measured_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.ForeignKeyConstraint(['parent_node_id'], ['remix_nodes.id'], ),
        sa.ForeignKeyConstraint(['evidence_snapshot_id'], ['evidence_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_events_event_id'), 'evidence_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_evidence_events_parent_node_id'), 'evidence_events', ['parent_node_id'], unique=False)
    
    # P0-5: Create decision_objects table
    op.create_table(
        'decision_objects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('decision_id', sa.String(length=100), nullable=False),
        sa.Column('evidence_event_id', sa.UUID(), nullable=False),
        sa.Column('decision_type', sa.Enum('GO', 'STOP', 'PIVOT', name='decisiontype'), nullable=False),
        sa.Column('decision_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evidence_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('transcript_artifact_id', sa.UUID(), nullable=True),
        sa.Column('decided_by', sa.UUID(), nullable=True),
        sa.Column('decision_method', sa.String(length=50), nullable=False, server_default='auto'),
        sa.Column('decided_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evidence_event_id'], ['evidence_events.id'], ),
        sa.ForeignKeyConstraint(['transcript_artifact_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['decided_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decision_objects_decision_id'), 'decision_objects', ['decision_id'], unique=True)
    op.create_index(op.f('ix_decision_objects_evidence_event_id'), 'decision_objects', ['evidence_event_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema"""
    # P0-5: Drop decision_objects
    op.drop_index(op.f('ix_decision_objects_evidence_event_id'), 'decision_objects')
    op.drop_index(op.f('ix_decision_objects_decision_id'), 'decision_objects')
    op.drop_table('decision_objects')
    
    # P0-5: Drop evidence_events
    op.drop_index(op.f('ix_evidence_events_parent_node_id'), 'evidence_events')
    op.drop_index(op.f('ix_evidence_events_event_id'), 'evidence_events')
    op.drop_table('evidence_events')
    
    # P0-4: Drop pattern_library
    op.drop_index(op.f('ix_pattern_library_temporal_phase'), 'pattern_library')
    op.drop_index(op.f('ix_pattern_library_cluster_id'), 'pattern_library')
    op.drop_index(op.f('ix_pattern_library_pattern_id'), 'pattern_library')
    op.drop_table('pattern_library')
    
    # P0-4: Revert notebook_source_packs changes
    op.drop_constraint('fk_notebook_source_packs_run_id', 'notebook_source_packs', type_='foreignkey')
    op.drop_index(op.f('ix_notebook_source_packs_temporal_phase'), 'notebook_source_packs')
    op.drop_column('notebook_source_packs', 'run_id')
    op.drop_column('notebook_source_packs', 'inputs_hash')
    op.drop_column('notebook_source_packs', 'temporal_phase')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS decisiontype')
    op.execute('DROP TYPE IF EXISTS evidenceeventstatus')
