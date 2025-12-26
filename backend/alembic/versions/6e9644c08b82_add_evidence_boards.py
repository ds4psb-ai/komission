"""add_evidence_boards

Revision ID: 6e9644c08b82
Revises: 
Create Date: 2025-12-25 17:59:36.819700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6e9644c08b82'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add new models from models.py"""
    
    # === Evidence Boards (Phase B) ===
    op.create_table('evidence_boards',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('kpi_target', sa.String(length=255), nullable=True),
        sa.Column('conclusion', sa.Text(), nullable=True),
        sa.Column('winner_item_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'CONCLUDED', name='evidenceboardstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('concluded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_boards_owner_id'), 'evidence_boards', ['owner_id'], unique=False)
    
    op.create_table('evidence_board_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('board_id', sa.UUID(), nullable=False),
        sa.Column('outlier_item_id', sa.UUID(), nullable=True),
        sa.Column('remix_node_id', sa.UUID(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['evidence_boards.id'], ),
        sa.ForeignKeyConstraint(['outlier_item_id'], ['outlier_items.id'], ),
        sa.ForeignKeyConstraint(['remix_node_id'], ['remix_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_board_items_board_id'), 'evidence_board_items', ['board_id'], unique=False)
    
    # === Creator Persona System (Phase 3) ===
    op.create_table('creator_behavior_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creator_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.Enum('TEMPLATE_OPEN', 'SLOT_CHANGE', 'RUN_START', 'RUN_COMPLETE', 'REWATCH', 'ABANDON', 'EXPORT', 'QUEST_APPLY', 'CALIBRATION_CHOICE', name='behavioreventtype'), nullable=False),
        sa.Column('node_id', sa.UUID(), nullable=True),
        sa.Column('template_id', sa.UUID(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_creator_behavior_events_created_at'), 'creator_behavior_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_creator_behavior_events_creator_id'), 'creator_behavior_events', ['creator_id'], unique=False)
    
    op.create_table('creator_calibration_choices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creator_id', sa.UUID(), nullable=False),
        sa.Column('pair_id', sa.String(length=100), nullable=False),
        sa.Column('option_a_id', sa.String(length=100), nullable=False),
        sa.Column('option_b_id', sa.String(length=100), nullable=False),
        sa.Column('selected', sa.Enum('A', 'B', name='calibrationchoice'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_creator_calibration_choices_creator_id'), 'creator_calibration_choices', ['creator_id'], unique=False)
    
    op.create_table('creator_style_fingerprints',
        sa.Column('creator_id', sa.UUID(), nullable=False),
        sa.Column('style_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('signal_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('creator_id')
    )
    
    # === Pattern Clustering ===
    op.create_table('pattern_clusters',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('cluster_id', sa.String(length=100), nullable=False),
        sa.Column('cluster_name', sa.String(length=255), nullable=False),
        sa.Column('pattern_type', sa.String(length=50), nullable=False),
        sa.Column('member_count', sa.Integer(), nullable=False),
        sa.Column('avg_outlier_score', sa.Float(), nullable=True),
        sa.Column('representative_node_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['representative_node_id'], ['remix_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pattern_clusters_cluster_id'), 'pattern_clusters', ['cluster_id'], unique=True)
    
    # === Template System ===
    op.create_table('template_seeds',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('seed_id', sa.String(length=100), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('cluster_id', sa.String(length=100), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('prompt_version', sa.String(length=50), nullable=True),
        sa.Column('seed_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['remix_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_seeds_cluster_id'), 'template_seeds', ['cluster_id'], unique=False)
    op.create_index(op.f('ix_template_seeds_seed_id'), 'template_seeds', ['seed_id'], unique=True)
    
    op.create_table('template_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parent_node_id', sa.UUID(), nullable=True),
        sa.Column('seed_id', sa.UUID(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('template_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('performance_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_node_id'], ['remix_nodes.id'], ),
        sa.ForeignKeyConstraint(['seed_id'], ['template_seeds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('template_feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('template_version_id', sa.UUID(), nullable=True),
        sa.Column('node_id', sa.UUID(), nullable=True),
        sa.Column('creator_id', sa.UUID(), nullable=False),
        sa.Column('feedback_type', sa.Enum('TOO_HARD', 'TOO_EASY', 'UNCLEAR', 'GREAT', 'NEEDS_EXAMPLE', 'WRONG_TIMING', 'OTHER', name='feedbacktype'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('completion_status', sa.String(length=50), nullable=False),
        sa.Column('time_spent_sec', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['remix_nodes.id'], ),
        sa.ForeignKeyConstraint(['template_version_id'], ['template_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_feedback_creator_id'), 'template_feedback', ['creator_id'], unique=False)
    
    # === Add columns to existing tables ===
    op.add_column('notebook_library', sa.Column('analysis_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('notebook_library', sa.Column('schema_version', sa.String(length=20), nullable=True))
    op.add_column('outlier_items', sa.Column('outlier_score', sa.Float(), nullable=True))
    op.add_column('outlier_items', sa.Column('outlier_tier', sa.String(length=1), nullable=True))
    op.add_column('outlier_items', sa.Column('creator_avg_views', sa.Integer(), nullable=True))
    op.add_column('outlier_items', sa.Column('engagement_rate', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema"""
    # Drop columns from existing tables
    op.drop_column('outlier_items', 'engagement_rate')
    op.drop_column('outlier_items', 'creator_avg_views')
    op.drop_column('outlier_items', 'outlier_tier')
    op.drop_column('outlier_items', 'outlier_score')
    op.drop_column('notebook_library', 'schema_version')
    op.drop_column('notebook_library', 'analysis_schema')
    
    # Drop tables
    op.drop_index(op.f('ix_template_feedback_creator_id'), table_name='template_feedback')
    op.drop_table('template_feedback')
    op.drop_table('template_versions')
    op.drop_index(op.f('ix_template_seeds_seed_id'), table_name='template_seeds')
    op.drop_index(op.f('ix_template_seeds_cluster_id'), table_name='template_seeds')
    op.drop_table('template_seeds')
    op.drop_index(op.f('ix_pattern_clusters_cluster_id'), table_name='pattern_clusters')
    op.drop_table('pattern_clusters')
    op.drop_table('creator_style_fingerprints')
    op.drop_index(op.f('ix_creator_calibration_choices_creator_id'), table_name='creator_calibration_choices')
    op.drop_table('creator_calibration_choices')
    op.drop_index(op.f('ix_creator_behavior_events_creator_id'), table_name='creator_behavior_events')
    op.drop_index(op.f('ix_creator_behavior_events_created_at'), table_name='creator_behavior_events')
    op.drop_table('creator_behavior_events')
    op.drop_index(op.f('ix_evidence_board_items_board_id'), table_name='evidence_board_items')
    op.drop_table('evidence_board_items')
    op.drop_index(op.f('ix_evidence_boards_owner_id'), table_name='evidence_boards')
    op.drop_table('evidence_boards')
