"""P0_run_artifact_vdg_edge_models

Revision ID: 910b7429e156
Revises: 2b6f5a1f0a1c
Create Date: 2025-12-26 13:57:16.403155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '910b7429e156'
down_revision: Union[str, Sequence[str], None] = '2b6f5a1f0a1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - P0-1, P0-2, P0-3 models"""
    # P0-1: Create runs table
    op.create_table(
        'runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.String(length=100), nullable=False),
        sa.Column('run_type', sa.Enum('CRAWLER', 'ANALYSIS', 'CLUSTERING', 'EVIDENCE', 'SOURCE_PACK', 'PATTERN_SYNTHESIS', 'DECISION', 'BANDIT', name='runtype'), nullable=False),
        sa.Column('status', sa.Enum('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='runstatus'), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False),
        sa.Column('inputs_hash', sa.String(length=64), nullable=False),
        sa.Column('inputs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('result_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.String(length=100), nullable=True),
        sa.Column('parent_run_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_run_id'], ['runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_runs_run_id'), 'runs', ['run_id'], unique=True)
    op.create_index(op.f('ix_runs_idempotency_key'), 'runs', ['idempotency_key'], unique=False)
    
    # P0-1: Create artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('artifact_id', sa.String(length=100), nullable=False),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('artifact_type', sa.Enum('RAW_DATA', 'ANALYSIS_SCHEMA', 'CLUSTER_RESULT', 'SOURCE_PACK', 'PATTERN_LIBRARY', 'EVIDENCE_SNAPSHOT', 'DECISION_OBJECT', 'TRANSCRIPT', name='artifacttype'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('storage_type', sa.String(length=50), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=True),
        sa.Column('schema_version', sa.String(length=20), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('data_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artifacts_artifact_id'), 'artifacts', ['artifact_id'], unique=True)
    op.create_index(op.f('ix_artifacts_run_id'), 'artifacts', ['run_id'], unique=False)
    
    # P0-3: Create vdg_edges table
    op.create_table(
        'vdg_edges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parent_node_id', sa.UUID(), nullable=False),
        sa.Column('child_node_id', sa.UUID(), nullable=False),
        sa.Column('edge_type', sa.Enum('FORK', 'VARIATION', 'INSPIRED_BY', name='vdgedgetype'), nullable=False),
        sa.Column('edge_status', sa.Enum('CANDIDATE', 'CONFIRMED', 'REJECTED', name='vdgedgestatus'), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('evidence_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confirmed_by', sa.UUID(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('confirmation_method', sa.String(length=50), nullable=True),
        sa.Column('run_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_node_id'], ['remix_nodes.id'], ),
        sa.ForeignKeyConstraint(['child_node_id'], ['remix_nodes.id'], ),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vdg_edges_parent_node_id'), 'vdg_edges', ['parent_node_id'], unique=False)
    op.create_index(op.f('ix_vdg_edges_child_node_id'), 'vdg_edges', ['child_node_id'], unique=False)
    
    # P0-2: Add columns to outlier_items
    op.add_column('outlier_items', sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('outlier_items', sa.Column('canonical_url', sa.String(length=500), nullable=True))
    op.add_column('outlier_items', sa.Column('run_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_outlier_items_run_id', 'outlier_items', 'runs', ['run_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema"""
    # P0-2: Remove columns from outlier_items
    op.drop_constraint('fk_outlier_items_run_id', 'outlier_items', type_='foreignkey')
    op.drop_column('outlier_items', 'run_id')
    op.drop_column('outlier_items', 'canonical_url')
    op.drop_column('outlier_items', 'raw_payload')
    
    # P0-3: Drop vdg_edges table
    op.drop_index(op.f('ix_vdg_edges_child_node_id'), 'vdg_edges')
    op.drop_index(op.f('ix_vdg_edges_parent_node_id'), 'vdg_edges')
    op.drop_table('vdg_edges')
    
    # P0-1: Drop artifacts table
    op.drop_index(op.f('ix_artifacts_run_id'), 'artifacts')
    op.drop_index(op.f('ix_artifacts_artifact_id'), 'artifacts')
    op.drop_table('artifacts')
    
    # P0-1: Drop runs table
    op.drop_index(op.f('ix_runs_idempotency_key'), 'runs')
    op.drop_index(op.f('ix_runs_run_id'), 'runs')
    op.drop_table('runs')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS vdgedgestatus')
    op.execute('DROP TYPE IF EXISTS vdgedgetype')
    op.execute('DROP TYPE IF EXISTS artifacttype')
    op.execute('DROP TYPE IF EXISTS runstatus')
    op.execute('DROP TYPE IF EXISTS runtype')
